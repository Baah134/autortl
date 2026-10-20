"""The orchestrator: an explicit, resumable state machine.

States: PLANNING -> SCAFFOLDING -> GENERATING -> LADDER -> INTEGRATING
        -> SYNTHESIZING -> TIMING_DOCTOR -> EVALUATING -> (loop) -> DONE
Crash anywhere, resume exactly there via state.json (Karpathy rule IV/V).

The harness owns every decision below; LLM calls are function calls whose
outputs face deterministic verification before they influence anything.
"""
from __future__ import annotations
import json
import shutil
import hashlib
import time
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .config import RunConfig
from .spec import DesignSpec, ModuleSpec, Port, ResetSpec
from .linter import lint_spec, write_stub_project, top_verilog
from .static_checks import check as static_check
from .state import RunState, atomic_write_text
from .roles import Planner, Generator, Evaluator, TimingDoctor, Evaluation
from .budget import Budget
from .cache import MetricsCache, ArtifactCache, code_hash
from .triage import FailureKind, classify
from .metrics_gate import validate as gate_metrics, MetricsGateError
from .watchdog import inspect as watchdog_inspect
from .taxonomy import Taxonomy
from .bestofn import Candidate, mutation_prompts, dedupe, select
from .timing_doctor import diagnose
from . import vivado
from .vivado import advisor_digest
from .report_parser import VivadoMetrics, extract_message_ids
from .golden import GoldenModel, qualify_against_examples
from .tbgen import generate as generate_tb
from .tbqual import qualify as qualify_tb, mutate
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.client import declared_latency


class Orchestrator:
    def __init__(self, cfg: RunConfig, run_dir: Path | None = None):
        self.cfg = cfg
        self._scope = "initial"
        self._counts = {}
        self._journal_enabled = False
        if run_dir is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir = Path("logs") / f"run_v4_{ts}"
        run_dir = Path(run_dir).resolve()
        cfg.work_dir = run_dir
        self.state = RunState(run_dir)
        self.budget = Budget(cfg.max_llm_calls, cfg.max_vivado_minutes,
                             cfg.max_wall_minutes, run_dir / "budget.json")
        self.metrics_cache = MetricsCache(run_dir / "metrics_cache.json")
        self.artifact_cache = ArtifactCache(run_dir / "artifact_cache.json")
        self.taxonomy = Taxonomy(Path(__file__).resolve().parent.parent
                                 / "data" / "taxonomy.yaml")
        self.planner = Planner()
        self.generator = Generator()
        self.evaluator = Evaluator()
        self.doctor = TimingDoctor()

    # ------------------------------------------------------------------ resume
    def _snapshot(self, **kw) -> None:
        d = self.state.load_fsm() or {}
        d.update(kw)
        self.state.save_fsm(d)

    # ------------------------------------------------------------ entry points
    def run(self) -> dict:
        self._prepare_inputs()
        self._counts = {}
        self._journal_enabled = True
        saved = self.state.load_fsm()
        if saved and saved.get("phase") == "DONE":
            summary_path = self.state.run_dir / "run_summary.json"
            if hashlib.sha256(summary_path.read_bytes()).hexdigest() != saved.get("summary_sha256"):
                raise ValueError("Completed summary evidence is missing or modified")
            summary = json.loads(summary_path.read_text())
            winner = self.state.run_dir / f"{summary.get('top_module', self.cfg.top_module)}_best.v"
            if not winner.exists() or hashlib.sha256(winner.read_bytes()).hexdigest() != saved.get("best_sha256"):
                raise ValueError("Completed winner artifact is missing or modified")
            for name, digest in saved.get("final_artifacts", {}).items():
                path = Path(name)
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    raise ValueError("Completed report evidence is missing or modified")
            return summary
        if saved and saved.get("phase") not in (None, "DONE"):
            print(f"[resume] continuing from phase={saved['phase']} "
                  f"iter={saved.get('iteration', '?')}")
        try:
            if self.cfg.mode == "build":
                result = self._run_build(saved)
            else:
                result = self._run_optimize(saved)
        except RuntimeError as exc:
            if not str(exc).startswith(("LLM_BUDGET:", "TOOL_BUDGET:")):
                raise
            result = self._baseline_stop("budget_exhausted", str(exc))
        if result.get("status") != "done":
            atomic_write_text(self.state.run_dir / "run_summary.json", json.dumps(result, indent=2))
        return result

    def _prepare_inputs(self):
        """Freeze user inputs once; resume never follows changed external files."""
        implementation = {}
        root = Path(__file__).resolve().parents[1]
        for directory in (root / "autortl", root / "llm", root / "data", root / ".claude" / "skills"):
            for path in sorted(directory.rglob("*")):
                if path.is_file() and path.suffix in (".py", ".yaml", ".md", ".v"):
                    implementation[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        runtime_path = self.state.run_dir / "runtime.json"
        runtime = {"schema_version": 1, "python": sys.version, "implementation": implementation,
                   "tools": self._cache_context(None, [])["tools"]}
        if runtime_path.exists():
            if json.loads(runtime_path.read_text()) != runtime:
                raise ValueError("Harness or Python changed since checkpoint; do not silently regrade an existing run")
        else:
            atomic_write_text(runtime_path, json.dumps(runtime, indent=2))
        manifest_path = self.state.run_dir / "inputs.json"
        if manifest_path.exists():
            config_path = self.state.run_dir / "config.json"
            if not config_path.exists():
                raise ValueError("Frozen inputs require a complete saved configuration")
            frozen_config = RunConfig.load(config_path)
            mutable_paths = {"design_path", "testbench_path", "spec_path", "work_dir", "top_module"}
            for name, value in frozen_config.to_dict().items():
                if name not in mutable_paths and name != "schema_version" and getattr(self.cfg, name) != value:
                    raise ValueError("Resume configuration changed: " + name)
            for name in mutable_paths:
                setattr(self.cfg, name, getattr(frozen_config, name))
            manifest = json.loads(manifest_path.read_text())
            for name, item in manifest.items():
                path = Path(item["path"])
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError("Frozen input modified: " + name)
                setattr(self.cfg, name, path)
            return
        directory = self.state.run_dir / "inputs"
        directory.mkdir(exist_ok=True)
        manifest = {}
        for name in ("design_path", "testbench_path", "spec_path"):
            original = getattr(self.cfg, name)
            if original is not None and Path(original).is_file():
                target = directory / (name + Path(original).suffix)
                target.write_bytes(Path(original).read_bytes())
                manifest[name] = {"path": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
                setattr(self.cfg, name, target)
        self.cfg.save(self.state.run_dir / "config.json")
        atomic_write_text(manifest_path, json.dumps(manifest, indent=2))

    @staticmethod
    def _pack(value):
        if isinstance(value, FailureKind):
            return {"__kind": "failure", "value": value.value}
        if isinstance(value, VivadoMetrics):
            return {"__kind": "metrics", "value": value.to_dict()}
        if isinstance(value, Evaluation):
            return {"__kind": "evaluation", "value": asdict(value)}
        if isinstance(value, tuple):
            return {"__kind": "tuple", "value": [Orchestrator._pack(v) for v in value]}
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, list):
            return [Orchestrator._pack(v) for v in value]
        if isinstance(value, dict):
            return {k: Orchestrator._pack(v) for k, v in value.items()}
        return value

    @staticmethod
    def _unpack(value):
        if isinstance(value, dict) and "__kind" in value:
            kind, data = value["__kind"], value["value"]
            if kind == "failure": return FailureKind(data)
            if kind == "metrics": return VivadoMetrics.from_dict(data)
            if kind == "evaluation": return Evaluation(**data)
            if kind == "tuple": return tuple(Orchestrator._unpack(v) for v in data)
        return value

    def _stage(self, category, name, function, args=(), kwargs=None, work=None, attempts=1):
        if not self._journal_enabled:
            return function()
        identity = f"{self._scope}:{category}:{name}"
        index = self._counts.get(identity, 0)
        self._counts[identity] = index + 1
        identity += f":{index}"
        directory = self.state.run_dir / "journal" / hashlib.sha256(identity.encode()).hexdigest()
        completion = directory / "completed.json"
        if completion.exists():
            saved = json.loads(completion.read_text())
            for relative, digest in saved.get("artifacts", {}).items():
                path = directory / "artifacts" / relative
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    raise ValueError("Stage evidence modified: " + identity)
                if work:
                    target = Path(work) / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(path.read_bytes())
            return self._unpack(saved["result"])
        directory.mkdir(parents=True, exist_ok=True)
        for attempt in range(attempts):
            previous = json.loads((directory / "started.json").read_text()) if (directory / "started.json").exists() else {}
            count = previous.get("attempt", 0) + 1
            atomic_write_text(directory / "started.json", json.dumps({"stage": identity,
                "args": repr(args), "kwargs": repr(kwargs), "attempt": count}, indent=2))
            self.state.append_event({"stage": identity, "attempt": count, "outcome": "RUNNING"},
                                    event_id=f"stage:{identity}:{count}:start")
            result = function()
            blocked = isinstance(result, tuple) and len(result) == 3 and result[0] is False and result[2] != FailureKind.DESIGN
            self.state.append_event({"stage": identity, "attempt": count,
                                     "outcome": "INFRA_FAIL" if blocked else "COMPLETE"},
                                    event_id=f"stage:{identity}:{count}:end")
            if not blocked:
                break
            if work:
                evidence = directory / f"failed_attempt_{count}"
                evidence.mkdir(exist_ok=True)
                for path in Path(work).glob("*.log"):
                    shutil.copyfile(path, evidence / path.name)
        # Infrastructure outcomes stay uncommitted, so a later resume can retry.
        if isinstance(result, tuple) and len(result) == 3 and result[0] is False and result[2] != FailureKind.DESIGN:
            return result
        artifacts = {}
        if work:
            for source in sorted(Path(work).rglob("*")):
                if source.is_file() and source.suffix in (".v", ".sv", ".rpt", ".log", ".tcl", ".xdc"):
                    relative = source.relative_to(work).as_posix()
                    target = directory / "artifacts" / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(source.read_bytes())
                    artifacts[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
        atomic_write_text(completion, json.dumps({"stage": identity, "result": self._pack(result),
                                                 "artifacts": artifacts}, indent=2))
        return result

    def _model(self, role, name, *args, **kwargs):
        return self._stage("model", role + "." + name,
                           lambda: getattr(getattr(self, role), name)(*args, **kwargs), args, kwargs)

    def _decision(self, name, function):
        return self._stage("decision", name, function)

    def _tool(self, name, *args, **kwargs):
        work_index = {"xvlog_check": 2, "xsim_run": 4, "run_synthesis": 3, "full_metrics": 0}[name]
        work = Path(args[work_index])
        def execute():
            if name != "full_metrics" and self._journal_enabled:
                if self.budget.wall_minutes >= self.budget.max_wall_minutes or self.budget.vivado_seconds >= self.budget.max_vivado_minutes * 60:
                    raise RuntimeError("TOOL_BUDGET: tool or wall-time budget exhausted")
                remaining = min((self.budget.max_wall_minutes - self.budget.wall_minutes) * 60,
                                self.budget.max_vivado_minutes * 60 - self.budget.vivado_seconds)
                default = {"xvlog_check": 120, "xsim_run": 300, "run_synthesis": 900}[name]
                kwargs["timeout"] = min(kwargs.get("timeout", default), remaining)
            started = time.monotonic()
            try:
                return getattr(vivado, name)(*args, **kwargs)
            finally:
                if name != "full_metrics":
                    self.budget.charge_vivado(max(time.monotonic() - started, vivado.vivado_seconds()))
        return self._stage("tool", name, execute, args, kwargs, work,
                           attempts=1 if name == "full_metrics" else self.cfg.max_infra_retries + 1)

    def _qualify_source(self, source, tb, name, work):
        """Record control and sabotage separately, without grading infra failures."""
        mutation = mutate(source)
        if mutation is None:
            contract = self._infer_contract(source, name)
            ports = ", ".join(f"{p.direction} wire [{p.width-1}:0] {p.name}" for p in contract.ports)
            outputs = [p for p in contract.ports if p.direction == "output"]
            if not outputs:
                return False, "no observable output to sabotage"
            mutated = "`timescale 1ns/1ps\nmodule " + name + "(" + ports + ");\n"
            mutated += "\n".join("assign " + p.name + " = 0;" for p in outputs) + "\nendmodule\n"
            mutation = mutated, "stuck-zero outputs"
        for label, code in (("control", source), ("mutant", mutation[0])):
            directory = work / "tbqual" / label
            directory.mkdir(parents=True, exist_ok=True)
            path = self._write_tmp(directory, name, code)
            passed, error, kind = self._tool("xsim_run", [path], tb, name + "_tb", self.cfg, directory)
            if label == "control" and not passed:
                return False, "qualification control did not pass: " + error
            if label == "mutant":
                qualified = not passed and kind == FailureKind.DESIGN and (
                    error.startswith("Testbench failures:") or error == "testbench reported failure")
                return qualified, ("detected " + mutation[1]) if qualified else "qualification not established: " + error

    # ------------------------------------------------------------- build mode
    def _run_build(self, saved: dict | None) -> dict:
        self._scope = "build_spec"
        # PHASE: SPEC
        self._snapshot(phase="PLANNING")
        intent = Path(self.cfg.spec_path).read_text()
        try:
            DesignSpec.from_json(intent)
            raw = intent
        except (ValueError, KeyError, TypeError):
            raw = self._model("planner", "make_spec", intent, self.cfg, self.budget)
        raw = raw[raw.find("{"): raw.rfind("}") + 1]
        self.state.spec_path.write_text(raw)
        spec = DesignSpec.load(self.state.spec_path)

        # PHASE: LINT + STUB ELABORATION (Pothole 1)
        errs = lint_spec(spec)
        if errs:
            self._snapshot(phase="PLANNING", lint_errors=errs)
            print("[lint] spec failed structural lint:")
            for e in errs:
                print("   -", e)
            return {"status": "spec_lint_failed", "errors": errs}
        stub_dir = self.state.run_dir / "stubs"
        stub_files = write_stub_project(spec, stub_dir)
        ok, err, kind = self._tool("xvlog_check", stub_files, self.cfg, stub_dir)
        if not ok:
            return {"status": "stub_elaboration_failed" if kind == FailureKind.DESIGN else "build_blocked", "error": err}

        # PHASE: PER-MODULE GENERATE + VERIFY (with artifact cache)
        module_files: dict[str, Path] = {}
        for m in spec.modules:
            self._scope = "module_" + m.name
            chash = m.contract_hash()
            cached = None  # completion journal retains verification; legacy cache cannot prove it
            mdir = self.state.run_dir / "modules" / m.name
            mdir.mkdir(parents=True, exist_ok=True)
            vfile = mdir / f"{m.name}.v"
            if cached:
                print(f"[cache] module {m.name} imported (contract hash {chash})")
                vfile.write_text(cached["verilog"])
                module_files[m.name] = vfile
                continue
            self._build_single = len(spec.modules) == 1
            self._build_top = spec.top_name
            result = self._build_module(m, mdir)
            if result is None:
                return {"status": "module_failed", "module": m.name}
            vfile.write_text(result)
            module_files[m.name] = vfile
            self.artifact_cache.put(chash, result, {})

        # PHASE: MECHANICAL INTEGRATION (zero LLM)
        self._scope = "build_integration"
        top_file = self.state.run_dir / "modules" / f"{spec.top_name}.v"
        top_file.write_text(top_verilog(spec))
        all_files = list(module_files.values()) + [top_file]
        ok, err, kind = self._tool("xvlog_check", all_files, self.cfg,
                                           self.state.run_dir / "modules")
        if not ok:
            return {"status": "integration_failed", "error": err}
        print("[build] integrated design compiles; entering optimize loop as baseline")

        # hand off to optimize with the integrated design
        self.cfg.top_module = spec.top_name
        self.cfg.design_path = top_file
        if not self.cfg.testbench_path:
            if len(spec.modules) != 1:
                return {"status": "build_blocked", "error": "Multi-module build requires trusted integration testbench"}
            child = spec.modules[0]
            child_tb = self.state.run_dir / "modules" / child.name / f"{child.name}_tb.v"
            adapted = re.sub(r"\b" + re.escape(child.name) + r"\b", spec.top_name, child_tb.read_text())
            adapted = re.sub(r"\b" + re.escape(child.name + "_tb") + r"\b", spec.top_name + "_tb", adapted)
            integration_tb = self.state.run_dir / f"{spec.top_name}_tb.v"
            integration_tb.write_text(adapted)
            self.cfg.testbench_path = integration_tb
        return self._run_optimize(None, extra_sources=list(module_files.values()))

    def _build_module(self, m: ModuleSpec, mdir: Path) -> str | None:
        """Generate one module through the ladder with best-of-N. Returns verilog."""
        print(f"[module {m.name}] golden model + testbench...")
        if getattr(self, "_build_single", False) and self.cfg.testbench_path:
            text = Path(self.cfg.testbench_path).read_text()
            text = re.sub(r"\b" + re.escape(self._build_top) + r"\b", m.name, text)
            text = re.sub(r"\b" + re.escape(self._build_top + "_tb") + r"\b", m.name + "_tb", text)
            tb = mdir / f"{m.name}_tb.v"
            tb.write_text(text)
            verilog = self._generate_verified(m, "", "Implement the exact supplied contract", tb, mdir)
            if verilog is None:
                return None
            qualified, _ = self._qualify_source(verilog, tb, m.name, mdir)
            return verilog if qualified else None
        golden_path = mdir / "golden.py"
        if self._journal_enabled or not golden_path.exists():
            golden_src = self._model("generator", "golden_model", m, self.budget)
            golden_path.write_text(golden_src)
        gm = GoldenModel(golden_path)
        gerrs = qualify_against_examples(gm, m)
        if gerrs:
            print(f"[module {m.name}] golden model failed spec examples: {gerrs}")
            # one regeneration attempt with the failures shown
            golden_src = self._model("generator", "golden_model", m, self.budget)
            golden_path.write_text(golden_src)
            gm = GoldenModel(golden_path)
            if qualify_against_examples(gm, m):
                return None
        tb = generate_tb(m, gm, mdir)
        verilog = self._generate_verified(m, "(initial implementation)",
                                          "", tb, mdir)
        if verilog is None:
            return None
        # testbench qualification against the now-good module (defence #7)
        qual_ok, reason = (self._qualify_source(verilog, tb, m.name, mdir)
                          if self._journal_enabled else qualify_tb(verilog, tb, m.name, self.cfg, mdir))
        print(f"[module {m.name}] tb qualification: {reason}")
        if not qual_ok:
            return None  # infra/unqualified stimulus must not silently change its own grading
        return verilog

    def _generate_verified(self, contract, seed, instruction, tb, directory):
        for mutation, prompt in mutation_prompts(self.cfg.objective, self.cfg.best_of_n):
            source = self._model("generator", "generate", contract, seed, instruction, prompt, self.budget)
            for attempt in range(self.cfg.max_fix_attempts + 1):
                result = static_check(source, contract)
                latency = declared_latency(source)
                if not result.passed or (latency is not None and latency != contract.latency):
                    break
                if "`timescale" not in source:
                    source = "`timescale 1ns/1ps\n" + source
                work = directory / f"candidate_{mutation}_{attempt}"
                work.mkdir(exist_ok=True)
                path = self._write_tmp(work, contract.name, source)
                ok, error, kind = self._tool("xvlog_check", [path], self.cfg, work)
                if ok:
                    ok, error, kind = self._tool("xsim_run", [path], tb, contract.name + "_tb", self.cfg, work)
                if ok:
                    self._write_tmp(directory, contract.name, source)
                    return source
                if kind != FailureKind.DESIGN:
                    return None
                if attempt < self.cfg.max_fix_attempts:
                    source = self._model("generator", "fix", source, "Repair without changing interface or latency",
                                         error, tb.read_text(), [], self.budget)
        return None

    def _write_tmp(self, mdir: Path, name: str, verilog: str) -> Path:
        p = mdir / f"{name}.v"
        p.write_text(verilog)
        return p

    # ---------------------------------------------------------- optimize mode
    def _run_optimize(self, saved: dict | None,
                      extra_sources: list[Path] | None = None) -> dict:
        cfg, state = self.cfg, self.state
        extra_sources = extra_sources or []

        # Verification is mandatory before even negotiating an optimization.
        if not cfg.testbench_path or not Path(cfg.testbench_path).is_file():
            return self._baseline_stop("baseline_blocked", "A baseline testbench is required")
        original = Path(cfg.design_path).read_text()
        # module contract for static checks in optimize mode (interface only)
        contract = self._infer_contract(original, cfg.top_module)

        self._scope = "baseline"
        # ---- iteration 0: baseline ----
        idir = state.iter_dir(0)
        base_v = idir / f"{cfg.top_module}.v"
        base_v.write_text(original)
        tb_path = Path(cfg.testbench_path) if cfg.testbench_path else None
        baseline = self._full_flow([base_v] + extra_sources, tb_path,
                                   cfg.top_module, idir)
        if not baseline.sim_passed or baseline.synth_error:
            print(f"[iter 0] baseline failed verification")
            v, baseline = self._fix_loop(original, baseline, tb_path,
                                         base_v, idir, extra_sources)
            if baseline.sim_passed and not baseline.synth_error:
                original = v
        if not baseline.sim_passed or baseline.synth_error:
            kind = self._flow_failure_kind(baseline)
            return self._baseline_stop(
                "baseline_failed" if kind == FailureKind.DESIGN else "baseline_blocked",
                baseline.sim_error or baseline.synth_error or "Baseline verification incomplete",
                kind)
        try:
            gate_metrics(baseline, synthesis_ran=True)
        except MetricsGateError as exc:
            return self._baseline_stop("baseline_blocked", str(exc), FailureKind.INFRA)
        state.append_design({"iteration": 0, "is_best": True,
                             **baseline.to_dict(), "recommendation": "BASELINE"})
        print(f"[iter 0] baseline LUTs={baseline.lut_used} FFs={baseline.ff_used} "
              f"WNS={baseline.wns_ns}")

        # ---- contract negotiation ----
        c = self._model("planner", "propose_contract", cfg.mode, cfg, baseline,
                                          original[:4000], self.budget)
        for review_round in range(3):
            fb = self._model("evaluator", "review_contract", c, self.budget)
            if re.match(r"^\s*ACCEPT(?:\s*:|\s*$)", fb, re.IGNORECASE):
                break
            if review_round == 2:
                state.write_contract(c)
                return self._baseline_stop("contract_blocked", "Contract rejected after three reviews: " + fb[:2000])
            c = self._model("planner", "refine_contract", c, fb, self.budget)
        state.write_contract(c)
        contract_md = state.read_contract()

        # ---- main loop ----
        best_v, best_m, best_iter = original, baseline, 0
        best_artifact_dir = idir
        generation_seed = original
        stall, replans, knobs_tried = 0, 0, False
        recent_codes: list[str] = []
        recent_errors: list[str] = []
        last_advisor = advisor_digest(idir, self.taxonomy)   # from baseline synth

        start_iter = 1  # reconstruct deterministically from completed stages
        for it in range(start_iter, cfg.max_iterations + 1):
            self._scope = f"iteration_{it}"
            if self._decision("exhausted", self.budget.exhausted):
                print("[budget] exhausted — stopping gracefully")
                break
            self._snapshot(phase="GENERATING", iteration=it,
                           best_iteration=best_iter)
            idir = state.iter_dir(it)

            # watchdog + planning
            signals = watchdog_inspect(state.read_designs(), recent_codes,
                                       recent_errors, self._decision("fraction", self.budget.fraction_left))
            for s in signals:
                print(f"[watchdog] {s.kind}: {s.detail}")
            need_plan = self._decision("need_plan", lambda: (it == start_iter or stall > 0 or it % 3 == 0
                         or any(s.kind == "STAGNATION" for s in signals)))
            if need_plan and self._decision("allow_replan", self.budget.allow_replan):
                plan = self._model("planner", "plan", it, contract_md, state.read_progress(),
                                         state.read_recent_evaluations(),
                                         best_m, signals, self.budget,
                                         target_part=cfg.target_part,
                                         advisor=last_advisor)
                state.write_plan(plan)
            instruction = self._decision("instruction", state.extract_instruction)

            # ---- best-of-N generation through the ladder ----
            n = self._decision("portfolio", lambda: self.budget.effective_best_of_n(cfg.best_of_n))
            cands: list[Candidate] = []
            for mname, mtext in mutation_prompts(cfg.objective, n):
                v = self._model("generator", "generate", contract, generation_seed, instruction,
                                            mtext, self.budget)
                cands.append(Candidate(verilog=v, mutation=mname))
            cands = dedupe(cands)
            recent_codes.extend(c.verilog for c in cands[:1])

            for c in cands:
                # rung 1: static
                sres = static_check(c.verilog, contract)
                if not sres.passed:
                    c.alive, c.fail_reason = False, "; ".join(sres.errors[:3])
                    continue
                c.ladder_rungs_passed = 1
                # latency law
                dl = declared_latency(c.verilog)
                if dl is not None and dl != contract.latency:
                    c.alive = False
                    c.fail_reason = (f"declared @latency {dl} != contract "
                                     f"{contract.latency} (spec is law)")
                    continue
                cdir = idir / f"cand_{c.mutation}"
                cdir.mkdir(exist_ok=True)
                cv = cdir / f"{cfg.top_module}.v"
                cv.write_text(c.verilog)
                # rung 2: xvlog
                ok, err, kind = self._tool("xvlog_check", [cv] + extra_sources,
                                                   self.cfg, cdir)
                if not ok:
                    if kind != FailureKind.DESIGN:
                        c.fail_reason = "infra: " + err[:100]
                        continue  # do not kill on infra; just no rung credit
                    c.alive, c.fail_reason = False, err[:200]
                    recent_errors.append(err)
                    continue
                c.ladder_rungs_passed = 2
                # rung 3/4: simulation
                if tb_path:
                    passed, err, kind = self._tool("xsim_run",
                        [cv] + extra_sources, tb_path,
                        f"{cfg.top_module}_tb", self.cfg, cdir)
                    if not passed:
                        if kind != FailureKind.DESIGN:
                            c.fail_reason = "infra: " + err[:100]
                            continue
                        # one taxonomy-guided fix per candidate
                        ids = extract_message_ids(err)
                        diag = "\n".join(self.taxonomy.repair_instruction(i)
                                         for i in ids) or "(no message IDs)"
                        c.verilog = self._model("generator", "fix",
                            c.verilog, diag, err,
                            tb_path.read_text()[:1500], [], self.budget)
                        repaired_static = static_check(c.verilog, contract)
                        repaired_latency = declared_latency(c.verilog)
                        if not repaired_static.passed or (repaired_latency is not None and repaired_latency != contract.latency):
                            c.alive, c.fail_reason = False, "repair violated static/interface/latency contract"
                            continue
                        cv.write_text(c.verilog)
                        passed, err, kind = self._tool("xsim_run",
                            [cv] + extra_sources, tb_path,
                            f"{cfg.top_module}_tb", self.cfg, cdir)
                        if not passed and kind != FailureKind.DESIGN:
                            c.fail_reason = "unverified: " + err[:100]
                            continue
                    if not passed:
                        c.alive, c.fail_reason = False, err[:200]
                        recent_errors.append(err)
                        continue
                    c.ladder_rungs_passed = 4

            # rung 5: synthesize survivors (cache-aware)
            for c in [x for x in cands if x.alive and x.ladder_rungs_passed == 4]:
                cache_context = self._cache_context(tb_path, extra_sources)
                cached_entry = self._stage("cache", c.mutation,
                    lambda: self.metrics_cache.get_entry(c.verilog, cache_context))
                cached = cached_entry.get("metrics") if cached_entry else None
                if cached:
                    try:
                        cached_metrics = VivadoMetrics.from_dict(cached)
                        gate_metrics(cached_metrics, synthesis_ran=True)
                        if not cached_metrics.sim_passed or cached_metrics.synth_error:
                            raise MetricsGateError("Cache has no verified synthesis result")
                    except (MetricsGateError, TypeError, ValueError, AttributeError) as exc:
                        print(f"[cache] invalid metrics ignored: {exc}")
                    else:
                        c.metrics = cached_metrics.to_dict()
                        c.artifact_dir = Path(cached_entry["artifact_dir"])
                        c.ladder_rungs_passed = 5
                        continue
                cdir = idir / f"cand_{c.mutation}"
                cv = cdir / f"{cfg.top_module}.v"
                ok, err, kind = self._tool("run_synthesis",
                    [cv] + extra_sources, cfg.top_module, self.cfg, cdir,
                    promotions=self.taxonomy.promotions())
                if not ok:
                    if kind != FailureKind.DESIGN:
                        c.fail_reason = "infra: " + err[:100]
                        continue
                    c.alive, c.fail_reason = False, err[:200]
                    continue
                m = self._tool("full_metrics", cdir)
                m.sim_passed = True
                try:
                    gate_metrics(m, synthesis_ran=True)
                except MetricsGateError as e:
                    print(f"[gate] {e} — treating as infra, candidate keeps no metrics")
                    c.fail_reason = "infra: invalid metrics"
                    continue
                c.metrics = m.to_dict()
                c.ladder_rungs_passed = 5
                self.metrics_cache.put(c.verilog, c.metrics, context=cache_context, artifact_dir=cdir)

            winner = select(cands, cfg.objective)
            if winner is None or winner.ladder_rungs_passed < 5:
                if any(c.alive and c.ladder_rungs_passed < 5 for c in cands):
                    self._snapshot(phase="INFRA_BLOCKED", iteration=it, best_iteration=best_iter)
                    state.append_event({"stage": "candidate_ladder", "iteration": it,
                                        "outcome": "infra_blocked"}, event_id=f"infra:{it}")
                    return {"status": "infra_blocked", "iteration": it,
                            "best_iteration": best_iter, "best_metrics": best_m.to_dict(),
                            "run_dir": str(state.run_dir)}
                stall += 1
                state.append_progress(it, "no candidate survived the ladder", "REJECT")
                state.append_design({"iteration": it, "is_best": False,
                                     "recommendation": "REJECT",
                                     "sim_passed": False})
                continue
            wm = VivadoMetrics.from_dict(winner.metrics)

            # ---- Timing Doctor ----
            wdir = getattr(winner, "artifact_dir", idir / f"cand_{winner.mutation}")
            if not wm.timing_met:
                diagd = diagnose(wdir, knobs_tried)
                print(f"[doctor] wns={diagd.wns_ns} category={diagd.category.value} "
                      f"action={diagd.action}")
                if diagd.action == "tool_knobs":
                    knobs_tried = True
                if diagd.action in ("tool_knobs", "rtl_surgery"):
                    trial = self._doctor_trial(winner.verilog, wm, contract, tb_path,
                                                extra_sources, idir, diagd)
                    if trial is not None:
                        winner.verilog, wm, wdir = trial
                        winner.metrics = wm.to_dict()

            # ---- evaluation ----
            ladder_summary = "\n".join(
                f"- {c.mutation}: rungs={c.ladder_rungs_passed} "
                f"{'ALIVE' if c.alive else 'dead: ' + c.fail_reason[:80]}"
                for c in cands)
            vnotes = "\n".join(vivado.message_ids_in(wdir)[:10])
            ev = self._model("evaluator", "evaluate", it, contract_md, ladder_summary, wm,
                                         vnotes, stall,
                                         cfg.stall_restart_threshold, self.budget)
            state.write_evaluation(it, ev.raw)
            fresh = advisor_digest(wdir, self.taxonomy)
            if fresh:
                last_advisor = fresh

            improved = self._is_better(wm, best_m)
            is_best = ev.recommendation == "ACCEPT" and improved
            if is_best:
                best_v, best_m, best_iter = winner.verilog, wm, it
                best_artifact_dir = wdir
                generation_seed = best_v
                stall = 0
                print(f"[iter {it}] *** NEW BEST *** LUTs={wm.lut_used} "
                      f"FFs={wm.ff_used} WNS={wm.wns_ns}")
            else:
                stall += 1
                print(f"[iter {it}] {ev.recommendation} LUTs={wm.lut_used} "
                      f"(best iter {best_iter}, stall {stall})")

            state.append_progress(it, instruction[:150],
                                  ev.recommendation + (" [NEW BEST]" if is_best else ""))
            state.append_design({"iteration": it, "is_best": is_best,
                                 "recommendation": ev.recommendation,
                                 "artifact_dir": str(wdir),
                                 "code_hash": code_hash(winner.verilog),
                                 **wm.to_dict()})

            # ---- restart mechanism ----
            if (ev.recommendation == "RESTART"
                    and stall >= cfg.stall_restart_threshold
                    and replans < cfg.max_replans
                    and self._decision("allow_replan", self.budget.allow_replan)):
                replans += 1
                tried = "\n".join(
                    f"iter {d['iteration']}: {d.get('recommendation')} "
                    f"LUTs={d.get('lut_used')}"
                    for d in state.read_designs()[-8:])
                plan = self._model("planner", "restart_plan", contract_md, stall, tried,
                                                 best_m, self.budget)
                state.write_plan(plan)
                # A search restart changes the next seed, never the accepted winner.
                generation_seed = original
                stall, knobs_tried = 0, False
                print(f"[restart {replans}/{cfg.max_replans}] new direction planned")

        # ---- finish ----
        best_path = state.run_dir / f"{cfg.top_module}_best.v"
        atomic_write_text(best_path, best_v)
        summary = {"status": "done", "best_iteration": best_iter,
                   "top_module": cfg.top_module,
                   "best_metrics": best_m.to_dict(),
                   "baseline_metrics": baseline.to_dict(),
                   "best_artifact_dir": str(best_artifact_dir),
                   "best_code_hash": code_hash(best_v),
                   "run_dir": str(state.run_dir)}
        atomic_write_text(state.run_dir / "run_summary.json",
                          json.dumps(summary, indent=2, default=str))
        print(f"\nDONE — best from iter {best_iter}: LUTs={best_m.lut_used} "
              f"FFs={best_m.ff_used} WNS={best_m.wns_ns}")
        final_artifacts = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in Path(best_artifact_dir).glob("*")
                           if path.is_file() and path.suffix in (".v", ".sv", ".rpt", ".xdc", ".tcl")}
        self._snapshot(phase="DONE", best_iteration=best_iter,
                       best_sha256=hashlib.sha256(best_path.read_bytes()).hexdigest(),
                       summary_sha256=hashlib.sha256((state.run_dir / "run_summary.json").read_bytes()).hexdigest(),
                       final_artifacts=final_artifacts)
        return summary

    # ------------------------------------------------------------------ helpers
    def _doctor_trial(self, source: str, current: VivadoMetrics, contract: ModuleSpec,
                      tb: Path | None, extra: list[Path], parent: Path,
                      diagnosis) -> tuple[str, VivadoMetrics, Path] | None:
        """Validate an isolated experiment before replacing any verified artifacts."""
        surgery = diagnosis.action == "rtl_surgery"
        if surgery:
            if tb is None:
                return None
            source = self._model("doctor", "surgery", source, diagnosis.instruction,
                                         diagnosis.detail, self.budget)
            if not static_check(source, contract).passed:
                return None
            latency = declared_latency(source)
            if latency is not None and latency != contract.latency:
                return None
        work = parent / f"doctor_{diagnosis.action}_trial"
        work.mkdir(parents=True, exist_ok=True)
        vfile = work / f"{self.cfg.top_module}.v"
        vfile.write_text(source)
        if surgery:
            passed, _, _ = self._tool("xsim_run", [vfile] + extra, tb,
                                          f"{self.cfg.top_module}_tb", self.cfg, work)
            if not passed:
                return None
        ok, _, _ = self._tool("run_synthesis",
            [vfile] + extra, self.cfg.top_module, self.cfg, work,
            promotions=self.taxonomy.promotions(),
            retiming=not surgery, phys_opt=not surgery)
        if not ok:
            return None
        result = self._tool("full_metrics", work)
        result.sim_passed, result.sim_error = True, ""
        try:
            gate_metrics(result, synthesis_ran=True)
            if result.synth_error:
                raise MetricsGateError(result.synth_error)
        except MetricsGateError as exc:
            print(f"[doctor] invalid trial metrics: {exc}")
            return None
        objective_field = {"minimize_luts": "lut_used", "minimize_ffs": "ff_used",
                           "maximize_freq": "wns_ns", "minimize_power": "dynamic_power_w"}[
                               self.cfg.objective]
        timing_recovered = (result.timing_met and not current.timing_met
                            and getattr(result, objective_field) == getattr(current, objective_field))
        if not self._is_better(result, current) and not timing_recovered:
            return None
        return source, result, work

    def _baseline_stop(self, status: str, error: str,
                       kind: FailureKind | None = None) -> dict:
        """Persist a non-success outcome without promoting or scoring a design."""
        summary = {"status": status, "error": error, "best_iteration": None,
                   "run_dir": str(self.state.run_dir)}
        if kind is not None:
            summary["failure_kind"] = kind.value
        self._snapshot(phase=status.upper(), best_iteration=None, error=error)
        atomic_write_text(self.state.run_dir / "run_summary.json", json.dumps(summary, indent=2))
        return summary

    def _flow_failure_kind(self, metrics: VivadoMetrics) -> FailureKind:
        return getattr(self, "_last_flow_failure_kind", None) or classify(
            metrics.sim_error or metrics.synth_error)

    def _full_flow(self, sources: list[Path], tb: Path | None, top: str,
                   work: Path) -> VivadoMetrics:
        self._last_flow_failure_kind = None
        m = VivadoMetrics()
        if tb:
            passed, err, kind = self._tool("xsim_run", sources, tb, f"{top}_tb",
                                             self.cfg, work)
            m.sim_passed, m.sim_error = passed, err
            if not passed:
                self._last_flow_failure_kind = kind
                return m
        else:
            m.sim_error = "A baseline testbench is required"
            self._last_flow_failure_kind = FailureKind.UNKNOWN
            return m
        ok, err, kind = self._tool("run_synthesis", sources, top, self.cfg, work,
                                          promotions=self.taxonomy.promotions())
        if not ok:
            m.synth_error = err
            self._last_flow_failure_kind = kind
            return m
        m2 = self._tool("full_metrics", work)
        m2.sim_passed = m.sim_passed
        m2.sim_error = m.sim_error
        return m2

    def _fix_loop(self, verilog: str, m: VivadoMetrics, tb: Path | None,
                  vfile: Path, work: Path,
                  extra: list[Path]) -> tuple[str, VivadoMetrics]:
        previous: list[str] = []
        original_contract = self._infer_contract(verilog, self.cfg.top_module)
        for _ in range(self.cfg.max_fix_attempts):
            if m.sim_passed and not m.synth_error:
                break
            if self._flow_failure_kind(m) != FailureKind.DESIGN:
                break
            err = m.sim_error or m.synth_error or "unknown"
            ids = extract_message_ids(err)
            diag = "\n".join(self.taxonomy.repair_instruction(i)
                             for i in ids) or "(no message IDs found)"
            repaired = self._model("generator", "fix", verilog, diag, err,
                                         tb.read_text()[:1500] if tb else "",
                                         previous, self.budget)
            latency = declared_latency(repaired)
            if not static_check(repaired, original_contract).passed or (
                    latency is not None and latency != original_contract.latency):
                m.sim_passed = False
                m.sim_error = "Repair violated static/interface/latency contract"
                self._last_flow_failure_kind = FailureKind.DESIGN
                return verilog, m
            verilog = repaired
            previous.append(err[:200])
            vfile.write_text(verilog)
            m = self._full_flow([vfile] + extra, tb,
                                self.cfg.top_module, work)
        return verilog, m

    def _is_better(self, new: VivadoMetrics, best: VivadoMetrics) -> bool:
        if not new.sim_passed:
            return False
        if best.timing_met and not new.timing_met:
            return False
        obj = self.cfg.objective
        if obj == "minimize_luts":
            return new.lut_used < best.lut_used
        if obj == "minimize_ffs":
            return new.ff_used < best.ff_used
        if obj == "maximize_freq":
            return new.wns_ns > best.wns_ns
        if obj == "minimize_power":
            return new.dynamic_power_w < best.dynamic_power_w
        return new.lut_used < best.lut_used

    def _infer_contract(self, verilog: str, top: str) -> ModuleSpec:
        from .verilog_interface import infer_module
        return infer_module(verilog, top)

    def _cache_context(self, tb, extra):
        def identity(path):
            path = Path(path)
            return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} if path.is_file() else {"executable": str(path)}
        return {"tb": identity(tb) if tb else None,
                "dependencies": [identity(p) for p in extra],
                "top": self.cfg.top_module, "part": self.cfg.target_part,
                "period_ns": self.cfg.target_period_ns,
                "tools": {name: identity(shutil.which(getattr(self.cfg, name)) or getattr(self.cfg, name))
                          for name in ("vivado_bin", "xvlog_bin", "xelab_bin", "xsim_bin")},
                "promotions": self.taxonomy.promotions(),
                "synthesis_template": hashlib.sha256(vivado.SYNTH_TCL.encode()).hexdigest()}
