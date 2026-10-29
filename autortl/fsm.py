"""The orchestrator: an explicit, resumable state machine.

States: PLANNING -> SCAFFOLDING -> GENERATING -> LADDER -> INTEGRATING
        -> SYNTHESIZING -> TIMING_DOCTOR -> EVALUATING -> (loop) -> DONE
Replay verified completed stages from durable checkpoints. External processes,
hard termination and budget accounting are not one atomic transaction.

The harness owns every decision below; LLM calls are function calls whose
outputs face deterministic verification before they influence anything.
"""
from __future__ import annotations
import json
import shutil
import hashlib
import time
import re
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .config import RunConfig
from .contract_context import run_evidence, file_evidence, flow_evidence, save_evidence, render_fixed_optimize_contract, tool_exit_evidence
from .spec import DesignSpec, ModuleSpec, Port, ResetSpec
from .linter import lint_spec, write_stub_project, top_verilog
from .static_checks import check as static_check
from .state import RunState, atomic_write_text
from .roles import Planner, Generator, Evaluator, TimingDoctor, Evaluation
from .budget import Budget
from .cache import MetricsCache, code_hash
from .triage import FailureKind, classify
from .metrics_gate import validate as gate_metrics, MetricsGateError
from .watchdog import inspect as watchdog_inspect
from .taxonomy import Taxonomy
from .bestofn import Candidate, mutation_prompts, dedupe, select
from .objectives import improvement_kind, timing_feasible
from .candidate_context import candidate_scope
from .proposal_feedback import record_candidate, render_feedback, source_identity, doctor_summary
from .timing_doctor import diagnose, TimingCategory
from . import vivado
from . import companions
from .vivado import advisor_digest
from .report_parser import VivadoMetrics, extract_message_ids
from .golden import GoldenModel, qualify_against_examples, validate_examples
from .tbgen import generate as generate_tb
from .tbqual import qualify as qualify_tb, assertion_failure_proof, qualification_mutations
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.client import declared_latency, ModelCallError


class VerificationEvidenceError(ValueError):
    """Previously verified inputs or receipts no longer establish a valid lineage."""


def _verification_inputs(sources, tb):
    def identity(path):
        path = Path(path)
        return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return {"schema_version": 1, "sources": [identity(path) for path in sources],
            "testbench": identity(tb) if tb is not None else None}


def _verification_dependencies(manifest: Path) -> dict[str, str]:
    """Bind simulated sources and TB to their recorded identities, not current guesses."""
    try:
        data = json.loads(Path(manifest).read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or type(data.get("schema_version")) is not int or
                data.get("schema_version") != 1 or
                not isinstance(data.get("sources"), list) or not data["sources"] or
                not isinstance(data.get("testbench"), dict)):
            raise ValueError("unsupported or incomplete verification input manifest")
        dependencies = {}
        for entry in [*data["sources"], data["testbench"]]:
            if (not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or
                    not Path(entry["path"]).is_absolute() or
                    not isinstance(entry.get("sha256"), str) or
                    not re.fullmatch(r"[a-f0-9]{64}", entry["sha256"])):
                raise ValueError("invalid verification dependency identity")
            path = Path(entry["path"])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise VerificationEvidenceError("Completed verification dependency missing or modified: " + str(path))
            dependencies[str(path.resolve())] = entry["sha256"]
        return dependencies
    except VerificationEvidenceError:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise VerificationEvidenceError("Completed verification dependency manifest is missing or invalid: " + str(manifest)) from exc


def _process_exit_gate(directory, provenance=None):
    """Require actual latest successful exits; model judgment cannot waive these."""
    reasons = []
    scopes = [(Path(directory), ("vivado",))] if provenance else [(Path(directory), ("xvlog", "xelab", "xsim", "vivado"))]
    if provenance:
        scopes.append((Path(provenance["prior_directory"]), ("xvlog", "xelab", "xsim")))
    for root, required in scopes:
        evidence = tool_exit_evidence(root)
        if not evidence["schema_valid"]:
            reasons.append(f"{root}: process exit receipts {evidence['status']}")
            continue
        records = [json.loads(line) for line in Path(evidence["path"]).read_bytes().splitlines()]
        for name in required:
            latest = next((item for item in reversed(records) if item["tool"] == name), None)
            if latest is None or not evidence["latest_by_tool"].get(name, {}).get("successful"):
                reasons.append(f"{root}: latest {name} exit is missing or unsuccessful")
                continue
            log = Path(latest["output_log_path"])
            if Path(latest["cwd"]).resolve() != root.resolve():
                reasons.append(f"{root}: {name} receipt belongs to another work directory")
            if not log.is_file() or hashlib.sha256(log.read_bytes()).hexdigest() != latest["output_log_sha256"]:
                reasons.append(f"{root}: {name} output evidence is missing or modified")
    return {"passed": not reasons, "reasons": reasons,
            "policy": "Every required tool's latest actual process exit must be zero with retained matching output; physical-only Doctor may reuse source-bound prior compile/simulation."}


def _doctor_advice(feedback):
    """Small preview; evaluation_facts retains the full bounded trial evidence."""
    summary = {key: feedback[key] for key in
               ("status", "reason", "action", "tools_ran") if key in feedback}
    metrics = feedback.get("measured_metrics")
    if metrics is not None:
        summary["measured_metrics"] = {key: metrics[key] for key in
            ("lut_used", "ff_used", "wns_ns", "whs_ns", "timing_met", "sim_passed") if key in metrics}
    parts = [json.dumps(summary, allow_nan=False)]
    source = feedback.get("trial_source", feedback.get("input_source"))
    if source is not None:
        parts.append("Trial RTL evidence: " + json.dumps({key: source[key] for key in ("path", "sha256")}))
        if source.get("text"):
            parts.append("RTL preview (bounded, not complete):\n" + source["text"][:1000])
    excerpt = feedback.get("first_violated_path_excerpt")
    if excerpt is not None:
        parts.append("Reported violated path (bounded): " + json.dumps({key: excerpt[key] for key in
            ("path", "sha256", "category", "slack_ns") if key in excerpt}) + "\n" + excerpt.get("text", "")[:1000])
    elif feedback.get("reports"):
        parts.append("Report identity: " + json.dumps(feedback["reports"][0]))
    text = "\n".join(parts)
    return ("Doctor trial evidence (advisory; NOT candidate/incumbent metrics):\n" +
            text[:2700] + ("\n[Preview truncated; complete trial record is in evaluation_facts.json.]"
                           if len(text) > 2700 else ""))


class Orchestrator:
    def __init__(self, cfg: RunConfig, run_dir: Path | None = None):
        self.cfg = cfg
        self._scope = "initial"
        self._counts = {}
        self._proposal_artifacts = {}
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
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
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
            try:
                if self.cfg.mode == "build":
                    result = self._run_build(saved)
                else:
                    result = self._run_optimize(saved)
            except VerificationEvidenceError as exc:
                best = self._verified_best_iteration()
                result = {"status": "infra_blocked", "failure_kind": FailureKind.INFRA.value,
                          "error": str(exc), "best_iteration": best, "run_dir": str(self.state.run_dir)}
                self._snapshot(phase="INFRA_BLOCKED", best_iteration=best, evidence_failure=[str(exc)])
                self.state.append_event({"stage": "verification_input_integrity", "outcome": "infra_blocked",
                                         "reason": str(exc)})
            except ModelCallError as exc:
                checkpoint = self.state.load_fsm() or {}
                # Baseline planning can fail before the first iteration snapshot.
                best = self._verified_best_iteration()
                result = {"status": "model_blocked", "failure_kind": FailureKind.INFRA.value,
                          "role": exc.role, "error_code": exc.code, "error": str(exc),
                          "diagnostics": exc.metadata, "run_dir": str(self.state.run_dir),
                          "best_iteration": best, "llm_calls": self.budget.llm_calls}
                self._snapshot(phase="MODEL_BLOCKED", blocked_phase=checkpoint.get("phase"),
                               best_iteration=best, error_code=exc.code, role=exc.role)
                self.state.append_event({"stage": "model_worker", "scope": self._scope,
                                         "outcome": "INFRA_FAIL", **result})
            except RuntimeError as exc:
                if not str(exc).startswith(("LLM_BUDGET:", "TOOL_BUDGET:")):
                    raise
                result = self._baseline_stop("budget_exhausted", str(exc))
            if result.get("status") != "done":
                atomic_write_text(self.state.run_dir / "run_summary.json", json.dumps(result, indent=2))
            return result
        finally:
            self.budget.checkpoint()

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
            if json.loads(runtime_path.read_text(encoding="utf-8")) != runtime:
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
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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
            saved = json.loads(completion.read_text(encoding="utf-8"))
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
            previous = json.loads((directory / "started.json").read_text(encoding="utf-8")) if (directory / "started.json").exists() else {}
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
                for path in Path(work).iterdir():
                    if path.is_file() and (path.suffix == ".log" or path.name in ("sim_log.txt", "qualification.json")):
                        shutil.copyfile(path, evidence / path.name)
        # Infrastructure outcomes stay uncommitted, so a later resume can retry.
        if isinstance(result, tuple) and len(result) == 3 and result[0] is False and result[2] != FailureKind.DESIGN:
            return result
        artifacts = {}
        if work:
            for source in sorted(Path(work).rglob("*")):
                if source.is_file() and (source.suffix in (".v", ".sv", ".rpt", ".log", ".tcl", ".xdc")
                                         or source.name in ("sim_log.txt", "qualification.json")):
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

    def _proposal_evidence(self, directory, name, data):
        """Journal chronological feedback and reject changed/missing saved context."""
        path = directory / f"proposal_{name}.json"
        serialized = json.dumps(data, sort_keys=True, indent=2, allow_nan=False)
        def persist():
            if path.exists() and path.read_text(encoding="utf-8") != serialized:
                raise VerificationEvidenceError("Proposal feedback evidence modified: " + str(path))
            atomic_write_text(path, serialized)
            return data
        expected = self._stage("proposal_feedback", name, persist)
        if (expected != data or not path.is_file()
                or path.read_text(encoding="utf-8") != serialized):
            raise VerificationEvidenceError("Proposal feedback evidence missing or modified: " + str(path))
        self._proposal_artifacts[str(path.resolve())] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return expected

    def _decision(self, name, function):
        return self._stage("decision", name, function)

    def _tool(self, name, *args, **kwargs):
        work_index = {"xvlog_check": 2, "xsim_run": 4, "run_synthesis": 3, "full_metrics": 0}[name]
        work = Path(args[work_index])
        inputs_before = _verification_inputs(args[0], args[1]) if name == "xsim_run" else None
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
                result = getattr(vivado, name)(*args, **kwargs)
                if name == "xsim_run" and result[0]:
                    # Commit verified inputs before the journal snapshots this stage.
                    if _verification_inputs(args[0], args[1]) != inputs_before:
                        raise VerificationEvidenceError("Simulation inputs changed during verification")
                    atomic_write_text(work / "verification_inputs.log", json.dumps(
                        inputs_before, sort_keys=True, indent=2))
                return result
            finally:
                if name != "full_metrics":
                    self.budget.charge_vivado(max(time.monotonic() - started, vivado.vivado_seconds()))
        result = self._stage("tool", name, execute, args, kwargs, work,
                             attempts=1 if name == "full_metrics" else self.cfg.max_infra_retries + 1)
        if name == "xsim_run" and result[0]:
            # A replay restores the original manifest; never restamp changed inputs
            # using an old success. Check pre-call inputs too, since stage replay
            # may restore an earlier source file into the working directory.
            manifest = work / "verification_inputs.log"
            if not manifest.is_file():
                raise VerificationEvidenceError("Simulation verified input manifest is missing")
            try:
                verified_inputs = json.loads(manifest.read_text(encoding="utf-8"))
                current_inputs = _verification_inputs(args[0], args[1])
            except (OSError, ValueError) as exc:
                raise VerificationEvidenceError("Simulation verified input manifest is invalid") from exc
            if verified_inputs != inputs_before or current_inputs != inputs_before:
                raise VerificationEvidenceError("Simulation replay inputs differ from verified input manifest")
        return result

    def _record_build_tool_block(self, error, kind, stage, tb=None):
        if kind != FailureKind.DESIGN:
            self._build_blocker = {"failure_kind": kind.value, "error": str(error)[:4000],
                                   "stage": stage, "testbench": str(Path(tb).resolve()) if tb else None}

    def _qualify_source(self, source, tb, name, work):
        """Require an observed assertion from a bounded, fully retained fault set."""
        faults = qualification_mutations(source, name)
        attempts, missed = [], []
        root = work / "tbqual"
        root.mkdir(parents=True, exist_ok=True)
        tb_hash = hashlib.sha256(Path(tb).read_bytes()).hexdigest() if Path(tb).is_file() else None

        def save(status, qualified=False):
            atomic_write_text(root / "qualification.json", json.dumps({
                "schema_version": 1, "status": status, "qualified": qualified,
                "testbench_sha256": tb_hash, "attempts": attempts, "missed": missed,
                "scope": "Minimum assertion sensitivity; missed faults remain coverage limits."}, indent=2))

        def run_case(label, code, description):
            directory = root / label
            directory.mkdir(parents=True, exist_ok=True)
            path = self._write_tmp(directory, name, code)
            passed, error, kind = self._tool("xsim_run", [path], tb, name + "_tb", self.cfg, directory)
            proof, detail = assertion_failure_proof(directory) if not passed else (False, "simulation passed")
            log = directory / "sim_log.txt"
            attempts.append({"label": label, "description": description, "passed": passed,
                "failure_kind": kind.value, "error": str(error)[:2000], "assertion_detected": proof,
                "proof_reason": detail, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "raw_log_sha256": hashlib.sha256(log.read_bytes()).hexdigest() if log.is_file() else None})
            return passed, error, kind, proof, detail

        if not faults:
            self._build_failure = "no observable output or supported fault to sabotage"
            save("unqualified")
            return False, self._build_failure
        passed, error, kind, _, _ = run_case("control", source, "unmodified control")
        if not passed or kind != FailureKind.DESIGN:
            self._build_failure = "qualification control did not pass: " + error
            self._record_build_tool_block(error, kind, "qualification control", tb)
            save("blocked" if kind != FailureKind.DESIGN else "control_failed")
            return False, self._build_failure
        save("qualifying")
        for label, code, description in faults:
            passed, error, kind, proof, detail = run_case(label, code, description)
            if kind != FailureKind.DESIGN:
                self._build_failure = "qualification tool blocked: " + error
                self._record_build_tool_block(error, kind, "qualification " + label, tb)
                save("blocked")
                return False, self._build_failure
            explicit_verdict = error.startswith("Testbench failures:") or error == "testbench reported failure"
            if not passed and explicit_verdict and proof:
                save("qualified", True)
                suffix = "; missed: " + ", ".join(item["description"] for item in missed) if missed else ""
                return True, "detected " + description + suffix
            missed.append({"label": label, "description": description,
                           "reason": "simulation passed" if passed else detail or error})
            save("qualifying")
        details = "; ".join(item["description"] + ": " + item["reason"] for item in missed)
        self._build_failure = "qualification not established; no tested fault produced retained assertion proof: " + details[:3000]
        save("unqualified")
        return False, self._build_failure

    # ------------------------------------------------------------- build mode
    def _run_build(self, saved: dict | None) -> dict:
        self._scope = "build_spec"
        # PHASE: SPEC
        self._snapshot(phase="PLANNING")
        intent = Path(self.cfg.spec_path).read_text(encoding="utf-8")
        try:
            DesignSpec.from_json(intent)
            raw = intent
        except (ValueError, KeyError, TypeError):
            raw = self._model("planner", "make_spec", intent, self.cfg, self.budget)
        raw = raw[raw.find("{"): raw.rfind("}") + 1]
        self.state.spec_path.write_text(raw, encoding="utf-8")
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

        # PHASE: PER-MODULE GENERATE + VERIFY (journal-backed evidence)
        module_files: dict[str, Path] = {}
        for m in spec.modules:
            self._scope = "module_" + m.name
            mdir = self.state.run_dir / "modules" / m.name
            mdir.mkdir(parents=True, exist_ok=True)
            vfile = mdir / f"{m.name}.v"
            self._build_single = len(spec.modules) == 1
            self._build_top = spec.top_name
            result = self._build_module(m, mdir)
            if result is None:
                blocker = getattr(self, "_build_blocker", None)
                if blocker:
                    return {"status": "build_blocked", "module": m.name, **blocker}
                return {"status": "module_failed", "module": m.name,
                        "error": getattr(self, "_build_failure", "module verification did not complete")}
            vfile.write_text(result, encoding="utf-8")
            module_files[m.name] = vfile

        # PHASE: MECHANICAL INTEGRATION (zero LLM)
        self._scope = "build_integration"
        top_file = self.state.run_dir / "modules" / f"{spec.top_name}.v"
        top_file.write_text(top_verilog(spec), encoding="utf-8")
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
            adapted = re.sub(r"\b" + re.escape(child.name) + r"\b", spec.top_name, child_tb.read_text(encoding="utf-8"))
            adapted = re.sub(r"\b" + re.escape(child.name + "_tb") + r"\b", spec.top_name + "_tb", adapted)
            integration_tb = self.state.run_dir / f"{spec.top_name}_tb.v"
            integration_tb.write_text(adapted, encoding="utf-8")
            self.cfg.testbench_path = integration_tb
        return self._run_optimize(None, extra_sources=list(module_files.values()))

    def _build_module(self, m: ModuleSpec, mdir: Path) -> str | None:
        """Generate one module through the ladder with best-of-N. Returns verilog."""
        self._build_blocker = None
        self._build_failure = "module verification did not complete"
        print(f"[module {m.name}] golden model + testbench...")
        independent_tb = None
        if getattr(self, "_build_single", False) and self.cfg.testbench_path:
            text = Path(self.cfg.testbench_path).read_text(encoding="utf-8")
            text = re.sub(r"\b" + re.escape(self._build_top) + r"\b", m.name, text)
            text = re.sub(r"\b" + re.escape(self._build_top + "_tb") + r"\b", m.name + "_tb", text)
            prefix = "independent_" if self.cfg.generate_golden else ""
            trusted_tb = mdir / f"{prefix}{m.name}_tb.v"
            trusted_tb.write_text(text, encoding="utf-8")
            if not self.cfg.generate_golden:
                verilog = self._generate_verified(m, "", "Implement the exact supplied contract", trusted_tb, mdir)
                if verilog is None:
                    return None
                qualified, _ = self._qualify_source(verilog, trusted_tb, m.name, mdir)
                return verilog if qualified else None
            independent_tb = trusted_tb
        example_errors = validate_examples(m, require_anchors=True)
        if example_errors:
            self._build_failure = "; ".join(example_errors[:20])
            atomic_write_text(mdir / "golden_qualification.log", json.dumps({
                "status": "invalid_spec_examples", "errors": [error[:1000] for error in example_errors[:20]],
                "model_calls": 0}, indent=2))
            return None
        golden_path = mdir / "golden.py"
        feedback = ""
        tb = None
        for attempt in range(1, 3):
            # Provider and storage failures propagate; only generated-program errors
            # enter this bounded oracle repair loop.
            if attempt == 1:
                golden_src = self._model("generator", "golden_model", m, self.budget)
            else:
                golden_src = self._model("generator", "golden_model", m, self.budget, feedback=feedback)
            golden_path.write_text(golden_src, encoding="utf-8")
            digest = hashlib.sha256(golden_path.read_bytes()).hexdigest()
            try:
                gm = GoldenModel(golden_path)
                errors = qualify_against_examples(gm, m)
                if errors:
                    raise ValueError("; ".join(errors[:10]))
                tb = generate_tb(m, gm, mdir)
            except (SyntaxError, ValueError, KeyError, TypeError) as exc:
                feedback = f"{type(exc).__name__}: {str(exc)[:2000]}"
                atomic_write_text(mdir / f"golden_attempt_{attempt}.log", json.dumps({
                    "attempt": attempt, "source_sha256": digest, "status": "oracle_rejected",
                    "diagnostic": feedback}, indent=2))
                continue
            atomic_write_text(mdir / f"golden_attempt_{attempt}.log", json.dumps({
                "attempt": attempt, "source_sha256": digest, "status": "oracle_qualified",
                "scope": "Specification examples and generated stimulus; not formal equivalence or reset-kind proof."}, indent=2))
            break
        else:
            self._build_failure = feedback
            return None
        verilog = self._generate_verified(m, "(initial implementation)",
                                          "", tb, mdir, independent_tb=independent_tb)
        if verilog is None:
            return None
        # testbench qualification against the now-good module (defence #7)
        qual_ok, reason = (self._qualify_source(verilog, tb, m.name, mdir)
                          if self._journal_enabled else qualify_tb(verilog, tb, m.name, self.cfg, mdir))
        print(f"[module {m.name}] tb qualification: {reason}")
        if not qual_ok:
            return None  # infra/unqualified stimulus must not silently change its own grading
        if independent_tb is not None:
            qualified, reason = self._qualify_source(verilog, independent_tb, m.name,
                                                      mdir / "independent_qualification")
            print(f"[module {m.name}] independent tb qualification: {reason}")
            if not qualified:
                return None
        return verilog

    def _generate_verified(self, contract, seed, instruction, tb, directory, *, independent_tb=None):
        for mutation, prompt in mutation_prompts(self.cfg.objective, self.cfg.best_of_n):
            source = self._model("generator", "generate", contract, seed, instruction, prompt, self.budget)
            for attempt in range(self.cfg.max_fix_attempts + 1):
                result = static_check(source, contract)
                latency = declared_latency(source, contract.name) if result.passed else None
                if not result.passed or (getattr(contract, "latency_known", True) and latency is not None and latency != contract.latency):
                    break
                if "`timescale" not in source:
                    source = "`timescale 1ns/1ps\n" + source
                work = directory / f"candidate_{mutation}_{attempt}"
                work.mkdir(exist_ok=True)
                path = self._write_tmp(work, contract.name, source)
                active_tb = tb
                ok, error, kind = self._tool("xvlog_check", [path], self.cfg, work)
                if ok:
                    ok, error, kind = self._tool("xsim_run", [path], tb, contract.name + "_tb", self.cfg, work)
                if ok and independent_tb is not None:
                    independent_work = work / "independent"
                    independent_work.mkdir(exist_ok=True)
                    active_tb = independent_tb
                    ok, error, kind = self._tool("xsim_run", [path], independent_tb,
                                                contract.name + "_tb", self.cfg, independent_work)
                if ok:
                    self._write_tmp(directory, contract.name, source)
                    return source
                if kind != FailureKind.DESIGN:
                    self._record_build_tool_block(error, kind,
                        "independent child verification" if active_tb == independent_tb else "child verification", active_tb)
                    return None
                self._build_failure = str(error)[:4000]
                if attempt < self.cfg.max_fix_attempts:
                    source = self._model("generator", "fix", source, "Repair without changing interface or latency",
                                         error, active_tb.read_text(encoding="utf-8"), [], self.budget)
        return None

    def _write_tmp(self, mdir: Path, name: str, verilog: str) -> Path:
        p = mdir / f"{name}.v"
        p.write_text(verilog, encoding="utf-8")
        return p

    # ---------------------------------------------------------- optimize mode
    def _run_optimize(self, saved: dict | None,
                      extra_sources: list[Path] | None = None) -> dict:
        cfg, state = self.cfg, self.state
        extra_sources = extra_sources or []

        # Verification is mandatory before defining an optimization contract.
        if not cfg.testbench_path or not Path(cfg.testbench_path).is_file():
            return self._baseline_stop("baseline_blocked", "A baseline testbench is required")
        original = Path(cfg.design_path).read_text(encoding="utf-8")
        # module contract for static checks in optimize mode (interface only)
        contract = self._infer_contract(original, cfg.top_module)

        self._scope = "baseline"
        # ---- iteration 0: baseline ----
        idir = state.iter_dir(0)
        base_v = idir / f"{cfg.top_module}.v"
        base_v.write_text(original, encoding="utf-8")
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
        baseline_receipts = _process_exit_gate(idir)
        if not baseline_receipts["passed"]:
            return self._baseline_stop("baseline_blocked", "; ".join(baseline_receipts["reasons"]), FailureKind.INFRA)
        state.append_design({"iteration": 0, "is_best": True,
                             **baseline.to_dict(), "recommendation": "BASELINE"})
        print(f"[iter 0] baseline LUTs={baseline.lut_used} FFs={baseline.ff_used} "
              f"WNS={baseline.wns_ns}")

        # ---- fixed harness contract: no model negotiation ----
        facts = run_evidence(cfg, baseline, [base_v] + extra_sources, tb_path,
                             idir, self._cache_context(tb_path, extra_sources),
                             **({"build_spec_path": state.spec_path} if cfg.mode == "build" else {}))
        context = save_evidence(state.run_dir / "harness_facts.json", facts)
        role_context = context + "\n\n" + candidate_scope(
            cfg.top_module, extra_sources, companions.required_by_testbench(tb_path, extra_sources))
        for role in (self.planner, self.generator, self.evaluator, self.doctor):
            role.run_context = role_context
        contract_md = render_fixed_optimize_contract(facts)
        if state.contract_path.exists():
            if state.read_contract() != contract_md:
                raise ValueError("Fixed optimization contract changed since checkpoint")
        else:
            if (state.load_fsm() or {}).get("contract_sha256"):
                raise ValueError("Fixed optimization contract missing since checkpoint")
            state.write_contract(contract_md)
        self._snapshot(contract_sha256=hashlib.sha256(contract_md.encode("utf-8")).hexdigest())

        # ---- main loop ----
        best_v, best_m, best_iter = original, baseline, 0
        best_artifact_dir = idir
        generation_seed = original
        plan_seed_sha256 = None
        termination_reason = None
        def planning_stop(iteration, seed, reason="planning_unavailable_for_generation_seed"):
            state.append_event({"stage": "planning", "iteration": iteration,
                                "outcome": "stopped", "reason": reason,
                                "seed_sha256": source_identity(seed),
                                "plan_seed_sha256": plan_seed_sha256},
                               event_id=f"planning_unavailable:{iteration}")
            return reason
        stall, replans, knobs_tried = 0, 0, False
        proposal_records = []  # reconstruct only completed earlier iterations during replay
        recent_codes: list[str] = []
        recent_errors: list[str] = []
        last_advisor = advisor_digest(idir, self.taxonomy)   # from baseline synth

        start_iter = 1  # reconstruct deterministically from completed stages
        for it in range(start_iter, cfg.max_iterations + 1):
            self._scope = f"iteration_{it}"
            if self._decision("exhausted", self.budget.exhausted):
                print("[budget] exhausted — stopping gracefully")
                if plan_seed_sha256 != source_identity(generation_seed):
                    termination_reason = planning_stop(it, generation_seed)
                break
            self._snapshot(phase="GENERATING", iteration=it,
                           best_iteration=best_iter)
            idir = state.iter_dir(it)

            # Snapshot only locally reconstructed past outcomes, never future disk history.
            proposal_context = render_feedback(proposal_records, generation_seed, it)
            self._proposal_evidence(idir, "input", {
                "schema_version": 1, "before_iteration": it,
                "seed_sha256": source_identity(generation_seed),
                "enabled": cfg.proposal_feedback,
                "feedback": proposal_context if cfg.proposal_feedback else ""})
            for role in (self.planner, self.generator):
                role.proposal_context = proposal_context if cfg.proposal_feedback else ""

            # watchdog + planning
            signals = watchdog_inspect(state.read_designs(), recent_codes,
                                       recent_errors, self._decision("fraction", self.budget.fraction_left))
            for s in signals:
                print(f"[watchdog] {s.kind}: {s.detail}")
            seed_sha256 = source_identity(generation_seed)
            need_plan = self._decision("need_plan", lambda: (plan_seed_sha256 != seed_sha256
                         or it == start_iter or stall > 0 or it % 3 == 0
                         or any(s.kind == "STAGNATION" for s in signals)))
            if need_plan and self._decision("allow_replan", self.budget.allow_replan):
                plan = self._model("planner", "plan", it, contract_md, state.read_progress(),
                                   state.read_recent_evaluations(), best_m, signals, self.budget,
                                   target_part=cfg.target_part, advisor=last_advisor,
                                   generation_seed=generation_seed)
                state.write_plan(plan)
                self._proposal_evidence(idir, "plan_binding", {
                    "schema_version": 1, "iteration": it,
                    "original_seed_sha256": source_identity(original),
                    "seed_sha256": seed_sha256,
                    "plan_sha256": source_identity(plan)})
                plan_seed_sha256 = seed_sha256
            if plan_seed_sha256 != seed_sha256:
                termination_reason = planning_stop(it, generation_seed)
                break
            # Always extract from the locally reconstructed, bound model result.
            # plan.md may contain a later iteration's plan during replay.
            state.write_plan(plan)
            instruction = self._decision("instruction", state.extract_instruction)

            # ---- best-of-N generation through the ladder ----
            n = self._decision("portfolio", lambda: self.budget.effective_best_of_n(cfg.best_of_n))
            cands: list[Candidate] = []
            for mname, mtext in mutation_prompts(cfg.objective, n):
                v = self._model("generator", "generate", contract, generation_seed, instruction,
                                            mtext, self.budget)
                cands.append(Candidate(verilog=v, mutation=mname))
            generated_sources = {c.mutation: c.verilog for c in cands}
            all_candidates = list(cands)
            cands = dedupe(cands)
            recent_codes.extend(c.verilog for c in cands[:1])

            for c in cands:
                self._verify_optimization_candidate(c, contract, tb_path, extra_sources,
                                                    idir, recent_errors)

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
                        c.cache_hit = True
                        c.metrics = cached_metrics.to_dict()
                        c.artifact_dir = Path(cached_entry["artifact_dir"])
                        c.ladder_rungs_passed = 5
                        continue
                cdir = getattr(c, "artifact_dir", idir / f"cand_{c.mutation}")
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

            standard_records = [
                record_candidate(c, generated_sources[c.mutation], instruction, it,
                                 cache_hit=getattr(c, "cache_hit", False))
                for c in all_candidates]
            winner = select(cands, cfg.objective)
            if winner is None or winner.ladder_rungs_passed < 5:
                if any(c.alive and c.ladder_rungs_passed < 5 for c in cands):
                    self._snapshot(phase="INFRA_BLOCKED", iteration=it, best_iteration=best_iter)
                    state.append_event({"stage": "candidate_ladder", "iteration": it,
                                        "outcome": "infra_blocked"}, event_id=f"infra:{it}")
                    return {"status": "infra_blocked", "iteration": it,
                            "best_iteration": best_iter, "best_metrics": best_m.to_dict(),
                            "run_dir": str(state.run_dir)}
                proposal_records.append(self._proposal_evidence(idir, "outcome", {
                    "schema_version": 1, "iteration": it, "instruction": instruction[:600],
                    "candidates": standard_records, "doctor": None,
                    "recommendation": "REJECT", "is_best": False,
                    "selected_source_sha256": None}))
                stall += 1
                state.append_progress(it, "no candidate survived the ladder", "REJECT")
                state.append_design({"iteration": it, "is_best": False,
                                     "recommendation": "REJECT",
                                     "sim_passed": False})
                continue
            wm = VivadoMetrics.from_dict(winner.metrics)

            # ---- Timing Doctor ----
            self._last_doctor_trial = None
            wdir = getattr(winner, "artifact_dir", idir / f"cand_{winner.mutation}")
            if not wm.timing_met:
                diagd = diagnose(wdir, knobs_tried)
                print(f"[doctor] wns={diagd.wns_ns} category={diagd.category.value} "
                      f"action={diagd.action}")
                if diagd.action == "tool_knobs":
                    knobs_tried = True
                if diagd.action in ("tool_knobs", "rtl_surgery"):
                    try:
                        trial = self._doctor_trial(winner.verilog, wm, contract, tb_path,
                                                    extra_sources, idir, diagd, verification_dir=Path(wdir))
                    except VerificationEvidenceError as exc:
                        self._snapshot(phase="INFRA_BLOCKED", iteration=it, best_iteration=best_iter,
                                       evidence_failure=[str(exc)])
                        state.append_event({"stage": "doctor_verification_lineage", "iteration": it,
                                            "outcome": "infra_blocked", "reason": str(exc)},
                                           event_id=f"doctor-evidence:{it}")
                        return {"status": "infra_blocked", "iteration": it,
                                "best_iteration": best_iter, "best_metrics": best_m.to_dict(),
                                "evidence_failure": [str(exc)], "run_dir": str(state.run_dir)}
                    if trial is not None:
                        winner.verilog, wm, wdir = trial
                        winner.metrics = wm.to_dict()

            # ---- evaluation ----
            ladder_summary = "\n".join(
                f"- {c.mutation}: rungs={c.ladder_rungs_passed} "
                f"{'ALIVE' if c.alive else 'dead: ' + c.fail_reason[:80]}"
                for c in cands)
            vnotes = "\n".join(vivado.message_ids_in(wdir)[:10])
            candidate_path = Path(wdir) / f"{cfg.top_module}.v"
            if not candidate_path.is_file():
                candidate_path = idir / f"cand_{winner.mutation}" / f"{cfg.top_module}.v"
            if candidate_path.read_text(encoding="utf-8") != winner.verilog:
                raise ValueError("Candidate source does not match evaluation evidence")
            candidate_facts = {
                "candidate_source": file_evidence(candidate_path),
                **flow_evidence(wdir),
                "candidate_metrics": wm.to_dict(), "previous_best_metrics": best_m.to_dict(),
                "objective": cfg.objective, "measured_improvement": self._is_better(wm, best_m),
                "improvement_kind": improvement_kind(wm, best_m, cfg.objective),
                "candidate_timing_feasible": timing_feasible(wm),
                "previous_best_timing_feasible": timing_feasible(best_m),
            }
            if self._last_doctor_trial is not None:
                candidate_facts["doctor_trial"] = self._last_doctor_trial
            provenance = None
            provenance_path = Path(wdir) / "verification_provenance.json"
            if provenance_path.is_file():
                provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
                if provenance.get("source_sha256") != hashlib.sha256(candidate_path.read_bytes()).hexdigest():
                    raise ValueError("Reused verification source does not match candidate evidence")
                for evidence in provenance["evidence"]:
                    path = Path(evidence["path"])
                    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != evidence["sha256"]:
                        raise ValueError("Reused verification evidence is missing or modified")
                candidate_facts["verification_reuse"] = provenance
            receipt_gate = _process_exit_gate(wdir, provenance)
            candidate_facts["process_exit_gate"] = receipt_gate
            self.evaluator.candidate_context = save_evidence(idir / "evaluation_facts.json", candidate_facts)
            if not receipt_gate["passed"]:
                self._snapshot(phase="INFRA_BLOCKED", iteration=it, best_iteration=best_iter,
                               evidence_failure=receipt_gate["reasons"])
                state.append_event({"stage": "process_exit_gate", "iteration": it,
                                    "outcome": "infra_blocked", "reasons": receipt_gate["reasons"]},
                                   event_id=f"exit-evidence:{it}")
                return {"status": "infra_blocked", "iteration": it,
                        "best_iteration": best_iter, "best_metrics": best_m.to_dict(),
                        "evidence_failure": receipt_gate["reasons"], "run_dir": str(state.run_dir)}
            ev = self._model("evaluator", "evaluate", it, contract_md, ladder_summary, wm,
                                         vnotes, stall,
                                         cfg.stall_restart_threshold, self.budget)
            state.write_evaluation(it, ev.raw)
            fresh = advisor_digest(wdir, self.taxonomy)
            if self._last_doctor_trial is not None:
                fresh = _doctor_advice(self._last_doctor_trial) + "\n\n" + fresh
            if fresh:
                last_advisor = fresh

            comparison_kind = improvement_kind(wm, best_m, cfg.objective)
            improved = comparison_kind is not None
            is_best = (receipt_gate["passed"] and ev.recommendation == "ACCEPT" and ev.failed == 0 and improved
                       and wm.timing_met is True and wm.wns_ns >= 0 and wm.whs_ns >= 0)
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
                                 "improvement_kind": comparison_kind if is_best else None,
                                 "artifact_dir": str(wdir),
                                 "code_hash": code_hash(winner.verilog),
                                 **wm.to_dict()})

            proposal_records.append(self._proposal_evidence(idir, "outcome", {
                "schema_version": 1, "iteration": it, "instruction": instruction[:600],
                "candidates": standard_records,
                "doctor": doctor_summary(self._last_doctor_trial),
                "recommendation": ev.recommendation, "is_best": is_best,
                "selected_source_sha256": source_identity(winner.verilog)}))

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
                restart_context = render_feedback(proposal_records, original, it + 1)
                self._proposal_evidence(idir, "restart", {
                    "schema_version": 1, "before_iteration": it + 1,
                    "seed_sha256": source_identity(original), "enabled": cfg.proposal_feedback,
                    "feedback": restart_context if cfg.proposal_feedback else ""})
                self.planner.proposal_context = restart_context if cfg.proposal_feedback else ""
                plan = self._model("planner", "restart_plan", contract_md, stall, tried,
                                   best_m, self.budget, generation_seed=original)
                state.write_plan(plan)
                self._proposal_evidence(idir, "restart_plan_binding", {
                    "schema_version": 1, "iteration": it,
                    "original_seed_sha256": source_identity(original),
                    "seed_sha256": source_identity(original),
                    "plan_sha256": source_identity(plan)})
                plan_seed_sha256 = source_identity(original)
                # A search restart changes the next seed, never the accepted winner.
                generation_seed = original
                stall, knobs_tried = 0, False
                print(f"[restart {replans}/{cfg.max_replans}] new direction planned")

        # ---- finish ----
        best_path = state.run_dir / f"{cfg.top_module}_best.v"
        summary = {"status": "done", "best_iteration": best_iter,
                   "timing_closed": timing_feasible(best_m),
                   "improvement_kind": improvement_kind(best_m, baseline, cfg.objective) if best_iter > 0 else None,
                   "top_module": cfg.top_module,
                   "best_metrics": best_m.to_dict(),
                   "baseline_metrics": baseline.to_dict(),
                   "best_artifact_dir": str(best_artifact_dir),
                   "best_code_hash": code_hash(best_v),
                   "run_dir": str(state.run_dir)}
        if termination_reason is not None:
            summary["termination_reason"] = termination_reason
        final_artifacts = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in Path(best_artifact_dir).glob("*")
                           if path.is_file() and (path.suffix in (".v", ".sv", ".rpt", ".xdc", ".tcl", ".log")
                                                 or path.name in ("tool_exit_records.log", "verification_provenance.json", "verification_inputs.log", "sim_log.txt"))}
        # Exit receipts remain mandatory evidence even when baseline wins or
        # Doctor only changes physical tool options in a separate directory.
        retained = list(state.run_dir.rglob("tool_exit_records.log"))
        # Retain negative assertion proof and missed-fault reports as well as
        # successful simulation receipts; both determine qualification.
        retained.extend(state.run_dir.rglob("qualification.json"))
        retained.extend(state.run_dir.rglob("sim_log.txt"))
        for receipt in list(retained):
            retained.extend(path for path in receipt.parent.glob("*.log") if path.is_file())
            if (receipt.parent / "sim_log.txt").is_file():
                retained.append(receipt.parent / "sim_log.txt")
        provenance_paths = set(state.run_dir.rglob("verification_provenance.json"))
        if (Path(best_artifact_dir) / "verification_provenance.json").is_file():
            provenance_paths.add(Path(best_artifact_dir) / "verification_provenance.json")
        verification_manifests = {path for path in state.run_dir.rglob("verification_inputs.log")
                                  if path.relative_to(state.run_dir).parts[0] != "journal"}
        best_manifest = Path(best_artifact_dir) / "verification_inputs.log"
        best_provenance = Path(best_artifact_dir) / "verification_provenance.json"
        if best_manifest.is_file():
            verification_manifests.add(best_manifest)
        elif not best_provenance.is_file():
            raise VerificationEvidenceError("Completed verification dependency manifest is missing: " + str(best_manifest))
        for provenance_path in provenance_paths:
            retained.append(provenance_path)
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            for evidence in provenance["evidence"]:
                path = Path(evidence["path"])
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != evidence["sha256"]:
                    raise ValueError("Reused verification evidence is missing or modified")
                retained.append(path)
                if path.name == "verification_inputs.log":
                    verification_manifests.add(path)
        for manifest in sorted(verification_manifests):
            final_artifacts.update(_verification_dependencies(manifest))
            retained.append(manifest)

        def retain_identity(identity, label):
            if (not isinstance(identity, dict) or not isinstance(identity.get("path"), str) or
                    not Path(identity["path"]).is_absolute() or
                    not isinstance(identity.get("sha256"), str) or
                    not re.fullmatch(r"[a-f0-9]{64}", identity["sha256"])):
                raise VerificationEvidenceError(label + " identity is invalid")
            path = Path(identity["path"])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != identity["sha256"]:
                raise VerificationEvidenceError(label + " missing or modified: " + str(path))
            final_artifacts[str(path.resolve())] = identity["sha256"]

        if facts.get("build_spec") is not None:
            retain_identity(facts["build_spec"], "Resolved build specification evidence")
        # Rejected Doctor reports still informed later plans. Retain their
        # originally observed digests, never freshly bless changed trial files.
        for evaluation_path in state.run_dir.glob("iter_*/evaluation_facts.json"):
            trial = json.loads(evaluation_path.read_text(encoding="utf-8")).get("doctor_trial")
            if trial is None:
                continue
            identities = [trial[key] for key in ("input_source", "trial_source", "prior_flow_script", "trial_flow_script") if key in trial]
            identities.extend(trial.get("reports", []))
            if trial.get("first_violated_path_excerpt") is not None:
                identities.append(trial["first_violated_path_excerpt"])
            for identity in identities:
                retain_identity(identity, "Doctor trial evidence")
        # Preserve observed feedback identities, including non-winning standard
        # flows that informed later proposals. Never bless changed bytes at DONE.
        for path, digest in self._proposal_artifacts.items():
            retain_identity({"path": path, "sha256": digest}, "Proposal feedback evidence")
        for record in proposal_records:
            for candidate in record["candidates"]:
                for key in ("source", "flow_script"):
                    if candidate.get(key) is not None:
                        retain_identity(candidate[key], "Standard proposal evidence")
        for evidence_path in [state.contract_path, state.run_dir / "harness_facts.json", *state.run_dir.glob("iter_*/evaluation_facts.json"), *state.run_dir.glob("iter_*/proposal_*.json"), *retained]:
            if evidence_path.is_file():
                final_artifacts[str(evidence_path.resolve())] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
        atomic_write_text(best_path, best_v)
        atomic_write_text(state.run_dir / "run_summary.json",
                          json.dumps(summary, indent=2, default=str))
        print(f"\nDONE — best from iter {best_iter}: LUTs={best_m.lut_used} "
              f"FFs={best_m.ff_used} WNS={best_m.wns_ns}")
        self._snapshot(phase="DONE", best_iteration=best_iter,
                       best_sha256=hashlib.sha256(best_path.read_bytes()).hexdigest(),
                       summary_sha256=hashlib.sha256((state.run_dir / "run_summary.json").read_bytes()).hexdigest(),
                       final_artifacts=final_artifacts)
        return summary

    # ------------------------------------------------------------------ helpers
    def _verify_optimization_candidate(self, candidate, contract, tb, extra, parent, recent_errors):
        """Spend only the configured design-repair budget across compile and sim.

        Infrastructure/unknown outcomes keep the candidate unverified, never
        mutate RTL, and remain replayable through the existing stage journal.
        Every changed answer re-enters static, interface, latency and tool gates.
        """
        base = parent / f"cand_{candidate.mutation}"
        previous = []
        for attempt in range(self.cfg.max_fix_attempts + 1):
            work = base if attempt == 0 else base / f"repair_{attempt:03d}"
            work.mkdir(parents=True, exist_ok=True)
            source = work / f"{self.cfg.top_module}.v"
            source.write_text(candidate.verilog, encoding="utf-8")
            candidate.artifact_dir = work
            candidate.ladder_rungs_passed = 0
            checked = static_check(candidate.verilog, contract)
            latency = declared_latency(candidate.verilog, contract.name) if checked.passed else None
            if not checked.passed:
                candidate.alive = False
                candidate.fail_reason = "; ".join(checked.errors[:3])
                return
            if getattr(contract, "latency_known", True) and latency is not None and latency != contract.latency:
                candidate.alive = False
                candidate.fail_reason = f"declared @latency {latency} != contract {contract.latency} (spec is law)"
                return
            candidate.ladder_rungs_passed = 1
            stale = companions.violation(candidate.verilog, self.cfg.top_module, extra, tb)
            if stale:
                # The testbench would grade a stale companion, not this candidate.
                ok, error, kind = False, stale, FailureKind.DESIGN
            else:
                ok, error, kind = self._tool("xvlog_check", [source] + extra, self.cfg, work)
            if ok:
                candidate.ladder_rungs_passed = 2
                if tb is None:
                    candidate.fail_reason = "unverified: a candidate testbench is required"
                    return
                ok, error, kind = self._tool("xsim_run", [source] + extra, tb,
                                            f"{self.cfg.top_module}_tb", self.cfg, work)
                if ok:
                    candidate.ladder_rungs_passed = 4
                    return
            if kind != FailureKind.DESIGN:
                candidate.fail_reason = "unverified: " + str(error)[:100]
                return
            recent_errors.append(error)
            if attempt >= self.cfg.max_fix_attempts:
                candidate.alive = False
                candidate.fail_reason = str(error)[:200]
                return
            diagnosis = "\n".join(self.taxonomy.repair_instruction(identifier)
                                   for identifier in extract_message_ids(error)) or "(no message IDs)"
            # The role also receives immutable run/edit-boundary context. Old
            # failures are advice; none changes the supplied testbench/contract.
            candidate.verilog = self._model("generator", "fix", candidate.verilog,
                diagnosis, error, tb.read_text(encoding="utf-8")[:1500] if tb else "",
                list(previous), self.budget)
            previous.append(str(error)[:200])

    def _doctor_default_flow(self, origin: Path, source: str, extra: list[Path], tb: Path) -> bool:
        """Prove exact prior RTL and default tool options, never infer from missing Tcl."""
        vfile, script = origin / f"{self.cfg.top_module}.v", origin / "synth.tcl"
        if not vfile.is_file() or not script.is_file():
            return False
        try:
            if vfile.read_bytes() != source.replace("\n", os.linesep).encode("utf-8"):
                return False
            if not _process_exit_gate(origin)["passed"]:
                return False
            manifest = origin / "verification_inputs.log"
            if json.loads(manifest.read_text(encoding="utf-8")) != _verification_inputs([vfile, *extra], tb):
                return False
            expected = vivado.SYNTH_TCL.format(
                promotions=vivado.promotion_tcl(self.taxonomy.promotions()),
                part=self.cfg.target_part,
                sources=" ".join(f'"{vivado._tcl_path(path)}"' for path in [vfile, *extra]),
                workdir=vivado._tcl_path(origin), period=f"{self.cfg.target_period_ns:.3f}",
                top=self.cfg.top_module, extra_synth="", phys_opt="")
            return script.read_text(encoding="utf-8") == expected
        except (OSError, UnicodeError, ValueError, TypeError, KeyError):
            return False

    def _doctor_trial(self, source: str, current: VivadoMetrics, contract: ModuleSpec,
                      tb: Path | None, extra: list[Path], parent: Path,
                      diagnosis, verification_dir: Path | None = None) -> tuple[str, VivadoMetrics, Path] | None:
        """Validate an isolated experiment before replacing any verified artifacts."""
        original_source = source
        self._last_doctor_trial = {
            "status": "NOT_ADOPTED", "action": diagnosis.action,
            "tools_ran": False, "reason": "not_verified",
            "scope": "Trial observations only; these do not replace candidate or incumbent metrics.",
        }
        feedback = self._last_doctor_trial
        if verification_dir is not None:
            prior = Path(verification_dir) / f"{self.cfg.top_module}.v"
            if prior.is_file():
                feedback["input_source"] = file_evidence(prior, 0)

        def finish(reason, *, metrics=None, adopted=False):
            feedback["reason"] = reason
            feedback["status"] = "ADOPTED" if adopted else "NOT_ADOPTED"
            if metrics is not None:
                feedback["measured_metrics"] = metrics.to_dict()
            if "work" in locations:
                evidence = flow_evidence(locations["work"])
                script = locations["work"] / "synth.tcl"
                if script.is_file():
                    feedback["trial_flow_script"] = file_evidence(script, 0)
                feedback["reports"] = evidence["report_manifest"][:8]
                feedback["reports_truncated"] = len(evidence["report_manifest"]) > 8
                excerpt = evidence.get("first_violated_path_excerpt")
                if excerpt is not None:
                    excerpt = dict(excerpt)
                    if len(excerpt.get("text", "")) > 2000:
                        excerpt["text"] = excerpt["text"][:2000]
                        excerpt["truncated"] = True
                    feedback["first_violated_path_excerpt"] = excerpt
            return None

        locations = {}
        surgery = diagnosis.action == "rtl_surgery"
        if surgery:
            if tb is None:
                return finish("missing_testbench")
            source = self._model("doctor", "surgery", source, diagnosis.instruction,
                                         diagnosis.detail, self.budget)
            feedback["proposed_source_text_sha256"] = hashlib.sha256(source.encode("utf-8")).hexdigest()
            if not static_check(source, contract).passed:
                return finish("static_or_interface_violation")
            latency = declared_latency(source, self.cfg.top_module)
            if getattr(contract, "latency_known", True) and latency is not None and latency != contract.latency:
                return finish("latency_violation")
            if (source == original_source and verification_dir is not None and
                    self._doctor_default_flow(Path(verification_dir), original_source, extra, tb)):
                feedback["input_source"] = file_evidence(Path(verification_dir) / f"{self.cfg.top_module}.v", 1000)
                feedback["prior_flow_script"] = file_evidence(Path(verification_dir) / "synth.tcl", 0)
                return finish("no_source_change")
        work = parent / f"doctor_{diagnosis.action}_trial"
        locations["work"] = work
        work.mkdir(parents=True, exist_ok=True)
        vfile = work / f"{self.cfg.top_module}.v"
        vfile.write_text(source, encoding="utf-8")
        feedback["trial_source"] = file_evidence(vfile, 1000)
        if not surgery and verification_dir is not None:
            origin = Path(verification_dir)
            origin_source = origin / f"{self.cfg.top_module}.v"
            if not origin_source.is_file() or origin_source.read_text(encoding="utf-8") != source:
                raise VerificationEvidenceError("Doctor verification reuse requires identical prior source")
            input_manifest = origin / "verification_inputs.log"
            if not input_manifest.is_file():
                raise VerificationEvidenceError("Doctor prior simulation input manifest is missing")
            try:
                verified_inputs = json.loads(input_manifest.read_text(encoding="utf-8"))
                current_inputs = _verification_inputs([origin_source, *extra], tb)
            except (OSError, ValueError) as exc:
                raise VerificationEvidenceError("Doctor prior simulation input evidence is invalid") from exc
            if verified_inputs != current_inputs:
                raise VerificationEvidenceError("Doctor prior simulation sources/testbench changed after verification")
            if hashlib.sha256(vfile.read_bytes()).hexdigest() != verified_inputs["sources"][0]["sha256"]:
                raise VerificationEvidenceError("Doctor trial bytes differ from verified source")
            prior_flow = flow_evidence(origin)
            evidence_paths = [input_manifest, origin_source, *extra]
            if tb is not None:
                evidence_paths.append(tb)
            evidence_paths += [path for path in origin.glob("*") if path.is_file() and
                (path.name == "tool_exit_records.log" or path.name.endswith("_log.txt") or path.name.endswith(".log"))]
            provenance = {
                "schema_version": 1, "mode": "source_identical_prior_verification",
                "source_sha256": hashlib.sha256(vfile.read_bytes()).hexdigest(),
                "prior_source_sha256": hashlib.sha256(origin_source.read_bytes()).hexdigest(),
                "prior_directory": str(origin.resolve()),
                "statement": "Only physical tool options changed. Compile/simulation were not rerun "
                             "in this directory; their actual prior evidence is reused for identical RTL, "
                             "testbench and companion sources. Missing prior exit receipts remain unknown.",
                "prior_flow_evidence": prior_flow,
                "evidence": [{"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                             for path in dict.fromkeys(evidence_paths)],
            }
            save_evidence(work / "verification_provenance.json", provenance)
        if surgery:
            feedback["tools_ran"] = True
            passed, _, _ = self._tool("xsim_run", [vfile] + extra, tb,
                                          f"{self.cfg.top_module}_tb", self.cfg, work)
            if not passed:
                return finish("simulation_not_verified")
        hold = getattr(diagnosis, "category", None) == TimingCategory.HOLD
        knobs = {"hold_fix": True} if hold else {}
        feedback["tools_ran"] = True
        ok, _, _ = self._tool("run_synthesis",
            [vfile] + extra, self.cfg.top_module, self.cfg, work,
            promotions=self.taxonomy.promotions(),
            retiming=not surgery and not hold, phys_opt=not surgery, **knobs)
        if not ok:
            return finish("synthesis_not_verified")
        result = self._tool("full_metrics", work)
        result.sim_passed, result.sim_error = True, ""
        try:
            gate_metrics(result, synthesis_ran=True)
            if result.synth_error:
                raise MetricsGateError(result.synth_error)
        except MetricsGateError as exc:
            print(f"[doctor] invalid trial metrics: {exc}")
            return finish("invalid_metrics")
        if not self._is_better(result, current):
            return finish("timing_not_closed" if not timing_feasible(result) else "no_policy_improvement", metrics=result)
        finish("policy_improvement", metrics=result, adopted=True)
        return source, result, work

    def _verified_best_iteration(self):
        for row in reversed(self.state.read_designs()):
            if row.get("is_best"):
                return row["iteration"]
        return (self.state.load_fsm() or {}).get("best_iteration")

    def _baseline_stop(self, status: str, error: str,
                       kind: FailureKind | None = None) -> dict:
        """Persist a non-success outcome without promoting or scoring a design."""
        best = self._verified_best_iteration()
        summary = {"status": status, "error": error, "best_iteration": best,
                   "run_dir": str(self.state.run_dir)}
        if kind is not None:
            summary["failure_kind"] = kind.value
        self._snapshot(phase=status.upper(), best_iteration=best, error=error)
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
                                         tb.read_text(encoding="utf-8")[:1500] if tb else "",
                                         previous, self.budget)
            checked = static_check(repaired, original_contract)
            latency = declared_latency(repaired, original_contract.name) if checked.passed else None
            if not checked.passed or (
                    getattr(original_contract, "latency_known", True) and latency is not None and latency != original_contract.latency):
                m.sim_passed = False
                m.sim_error = "Repair violated static/interface/latency contract"
                self._last_flow_failure_kind = FailureKind.DESIGN
                return verilog, m
            verilog = repaired
            previous.append(err[:200])
            vfile.write_text(verilog, encoding="utf-8")
            m = self._full_flow([vfile] + extra, tb,
                                self.cfg.top_module, work)
        return verilog, m

    def _is_better(self, new: VivadoMetrics, best: VivadoMetrics) -> bool:
        return improvement_kind(new, best, self.cfg.objective) is not None

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
