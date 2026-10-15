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
from datetime import datetime
from pathlib import Path

from .config import RunConfig
from .spec import DesignSpec, ModuleSpec, Port, ResetSpec
from .linter import lint_spec, write_stub_project, top_verilog
from .static_checks import check as static_check
from .state import RunState
from .roles import Planner, Generator, Evaluator, TimingDoctor, Evaluation
from .budget import Budget
from .cache import MetricsCache, ArtifactCache, code_hash
from .triage import FailureKind
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
from .tbqual import qualify as qualify_tb
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.client import declared_latency


class Orchestrator:
    def __init__(self, cfg: RunConfig, run_dir: Path | None = None):
        self.cfg = cfg
        if run_dir is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir = Path("logs") / f"run_v4_{ts}"
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
        saved = self.state.load_fsm()
        if saved and saved.get("phase") not in (None, "DONE"):
            print(f"[resume] continuing from phase={saved['phase']} "
                  f"iter={saved.get('iteration', '?')}")
        if self.cfg.mode == "build":
            return self._run_build(saved)
        return self._run_optimize(saved)

    # ------------------------------------------------------------- build mode
    def _run_build(self, saved: dict | None) -> dict:
        # PHASE: SPEC
        if not self.state.spec_path.exists():
            self._snapshot(phase="PLANNING")
            intent = Path(self.cfg.spec_path).read_text()
            raw = self.planner.make_spec(intent, self.cfg, self.budget)
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
        ok, err, kind = vivado.xvlog_check(stub_files, self.cfg, stub_dir)
        if not ok and kind == FailureKind.DESIGN:
            return {"status": "stub_elaboration_failed", "error": err}

        # PHASE: PER-MODULE GENERATE + VERIFY (with artifact cache)
        module_files: dict[str, Path] = {}
        for m in spec.modules:
            chash = m.contract_hash()
            cached = self.artifact_cache.get(chash)
            mdir = self.state.run_dir / "modules" / m.name
            mdir.mkdir(parents=True, exist_ok=True)
            vfile = mdir / f"{m.name}.v"
            if cached:
                print(f"[cache] module {m.name} imported (contract hash {chash})")
                vfile.write_text(cached["verilog"])
                module_files[m.name] = vfile
                continue
            result = self._build_module(m, mdir)
            if result is None:
                return {"status": "module_failed", "module": m.name}
            vfile.write_text(result)
            module_files[m.name] = vfile
            self.artifact_cache.put(chash, result, {})

        # PHASE: MECHANICAL INTEGRATION (zero LLM)
        top_file = self.state.run_dir / "modules" / f"{spec.top_name}.v"
        top_file.write_text(top_verilog(spec))
        all_files = list(module_files.values()) + [top_file]
        ok, err, kind = vivado.xvlog_check(all_files, self.cfg,
                                           self.state.run_dir / "modules")
        if not ok:
            return {"status": "integration_failed", "error": err}
        print("[build] integrated design compiles; entering optimize loop as baseline")

        # hand off to optimize with the integrated design
        self.cfg.top_module = spec.top_name
        self.cfg.design_path = top_file
        return self._run_optimize(None, extra_sources=list(module_files.values()))

    def _build_module(self, m: ModuleSpec, mdir: Path) -> str | None:
        """Generate one module through the ladder with best-of-N. Returns verilog."""
        print(f"[module {m.name}] golden model + testbench...")
        golden_path = mdir / "golden.py"
        if not golden_path.exists():
            golden_src = self.generator.golden_model(m, self.budget)
            golden_path.write_text(golden_src)
        gm = GoldenModel(golden_path)
        gerrs = qualify_against_examples(gm, m)
        if gerrs:
            print(f"[module {m.name}] golden model failed spec examples: {gerrs}")
            # one regeneration attempt with the failures shown
            golden_src = self.generator.golden_model(m, self.budget)
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
        qual_ok, reason = qualify_tb(verilog, tb, m.name, self.cfg, mdir)
        print(f"[module {m.name}] tb qualification: {reason}")
        if not qual_ok:
            # regenerate stimulus with a different seed and re-verify once
            tb = generate_tb(m, gm, mdir, seed=99991)
            passed, err, _ = vivado.xsim_run([mdir / f'{m.name}.v.tmp'
                                              if False else self._write_tmp(mdir, m.name, verilog)],
                                             tb, f"{m.name}_tb", self.cfg, mdir)
            if not passed:
                return None
            qual_ok, reason = qualify_tb(verilog, tb, m.name, self.cfg, mdir)
            if not qual_ok:
                return None
        return verilog

    def _write_tmp(self, mdir: Path, name: str, verilog: str) -> Path:
        p = mdir / f"{name}.v"
        p.write_text(verilog)
        return p

    # ---------------------------------------------------------- optimize mode
    def _run_optimize(self, saved: dict | None,
                      extra_sources: list[Path] | None = None) -> dict:
        cfg, state = self.cfg, self.state
        extra_sources = extra_sources or []

        original = Path(cfg.design_path).read_text()
        # module contract for static checks in optimize mode (interface only)
        contract = self._infer_contract(original, cfg.top_module)

        # ---- iteration 0: baseline ----
        idir = state.iter_dir(0)
        base_v = idir / f"{cfg.top_module}.v"
        base_v.write_text(original)
        tb_path = Path(cfg.testbench_path) if cfg.testbench_path else None
        baseline = self._full_flow([base_v] + extra_sources, tb_path,
                                   cfg.top_module, idir)
        if not baseline.sim_passed:
            print(f"[iter 0] baseline failed sim — attempting fixes")
            v, baseline = self._fix_loop(original, baseline, tb_path,
                                         base_v, idir, extra_sources)
            if baseline.sim_passed:
                original = v
        state.append_design({"iteration": 0, "is_best": True,
                             **baseline.to_dict(), "recommendation": "BASELINE"})
        print(f"[iter 0] baseline LUTs={baseline.lut_used} FFs={baseline.ff_used} "
              f"WNS={baseline.wns_ns}")

        # ---- contract negotiation ----
        if not state.read_contract():
            c = self.planner.propose_contract(cfg.mode, cfg, baseline,
                                              original[:4000], self.budget)
            for _ in range(3):
                fb = self.evaluator.review_contract(c, self.budget)
                if fb.upper().startswith("ACCEPT"):
                    break
                c = self.planner.refine_contract(c, fb, self.budget)
            state.write_contract(c)
        contract_md = state.read_contract()

        # ---- main loop ----
        best_v, best_m, best_iter = original, baseline, 0
        stall, replans, knobs_tried = 0, 0, False
        recent_codes: list[str] = []
        recent_errors: list[str] = []
        last_advisor = advisor_digest(idir, self.taxonomy)   # from baseline synth

        start_iter = (saved or {}).get("iteration", 1) if saved else 1
        for it in range(start_iter, cfg.max_iterations + 1):
            if self.budget.exhausted():
                print("[budget] exhausted — stopping gracefully")
                break
            self._snapshot(phase="GENERATING", iteration=it,
                           best_iteration=best_iter)
            idir = state.iter_dir(it)

            # watchdog + planning
            signals = watchdog_inspect(state.read_designs(), recent_codes,
                                       recent_errors, self.budget.fraction_left())
            for s in signals:
                print(f"[watchdog] {s.kind}: {s.detail}")
            need_plan = (it == start_iter or stall > 0 or it % 3 == 0
                         or any(s.kind == "STAGNATION" for s in signals))
            if need_plan and self.budget.allow_replan():
                plan = self.planner.plan(it, contract_md, state.read_progress(),
                                         state.read_recent_evaluations(),
                                         best_m, signals, self.budget,
                                         target_part=cfg.target_part,
                                         advisor=last_advisor)
                state.write_plan(plan)
            instruction = state.extract_instruction()

            # ---- best-of-N generation through the ladder ----
            n = self.budget.effective_best_of_n(cfg.best_of_n)
            cands: list[Candidate] = []
            for mname, mtext in mutation_prompts(cfg.objective, n):
                v = self.generator.generate(contract, best_v, instruction,
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
                ok, err, kind = vivado.xvlog_check([cv] + extra_sources,
                                                   self.cfg, cdir)
                self.budget.charge_vivado(vivado.vivado_seconds())
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
                    passed, err, kind = vivado.xsim_run(
                        [cv] + extra_sources, tb_path,
                        f"{cfg.top_module}_tb", self.cfg, cdir)
                    self.budget.charge_vivado(vivado.vivado_seconds())
                    if not passed:
                        if kind != FailureKind.DESIGN:
                            c.fail_reason = "infra: " + err[:100]
                            continue
                        # one taxonomy-guided fix per candidate
                        ids = extract_message_ids(err)
                        diag = "\n".join(self.taxonomy.repair_instruction(i)
                                         for i in ids) or "(no message IDs)"
                        c.verilog = self.generator.fix(
                            c.verilog, diag, err,
                            tb_path.read_text()[:1500], [], self.budget)
                        cv.write_text(c.verilog)
                        passed, err, kind = vivado.xsim_run(
                            [cv] + extra_sources, tb_path,
                            f"{cfg.top_module}_tb", self.cfg, cdir)
                        self.budget.charge_vivado(vivado.vivado_seconds())
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
                cached = self.metrics_cache.get(c.verilog)
                if cached:
                    c.metrics = cached
                    c.ladder_rungs_passed = 5
                    continue
                cdir = idir / f"cand_{c.mutation}"
                cv = cdir / f"{cfg.top_module}.v"
                ok, err, kind = vivado.run_synthesis(
                    [cv] + extra_sources, cfg.top_module, self.cfg, cdir,
                    promotions=self.taxonomy.promotions())
                self.budget.charge_vivado(vivado.vivado_seconds())
                if not ok:
                    if kind == FailureKind.INFRA:
                        continue
                    c.alive, c.fail_reason = False, err[:200]
                    continue
                m = vivado.full_metrics(cdir)
                m.sim_passed = True
                try:
                    gate_metrics(m, synthesis_ran=True)
                except MetricsGateError as e:
                    print(f"[gate] {e} — treating as infra, candidate keeps no metrics")
                    continue
                c.metrics = m.to_dict()
                c.ladder_rungs_passed = 5
                self.metrics_cache.put(c.verilog, c.metrics)

            winner = select(cands, cfg.objective)
            if winner is None or winner.ladder_rungs_passed < 5:
                stall += 1
                state.append_progress(it, "no candidate survived the ladder", "REJECT")
                state.append_design({"iteration": it, "is_best": False,
                                     "recommendation": "REJECT",
                                     "sim_passed": False})
                continue
            wm = VivadoMetrics.from_dict(winner.metrics)

            # ---- Timing Doctor ----
            wdir = idir / f"cand_{winner.mutation}"
            if not wm.timing_met:
                diagd = diagnose(wdir, knobs_tried)
                print(f"[doctor] wns={diagd.wns_ns} category={diagd.category.value} "
                      f"action={diagd.action}")
                if diagd.action == "tool_knobs":
                    knobs_tried = True
                    ok, err, _ = vivado.run_synthesis(
                        [wdir / f"{cfg.top_module}.v"] + extra_sources,
                        cfg.top_module, self.cfg, wdir,
                        promotions=self.taxonomy.promotions(),
                        retiming=True, phys_opt=True)
                    self.budget.charge_vivado(vivado.vivado_seconds())
                    if ok:
                        wm = vivado.full_metrics(wdir)
                        wm.sim_passed = True
                elif diagd.action == "rtl_surgery":
                    fixed = self.doctor.surgery(winner.verilog, diagd.instruction,
                                                diagd.detail, self.budget)
                    sres = static_check(fixed, contract)
                    if sres.passed:
                        (wdir / f"{cfg.top_module}.v").write_text(fixed)
                        # surgery faces the ladder like any candidate
                        passed = True
                        if tb_path:
                            passed, err, _ = vivado.xsim_run(
                                [wdir / f"{cfg.top_module}.v"] + extra_sources,
                                tb_path, f"{cfg.top_module}_tb", self.cfg, wdir)
                        if passed:
                            ok, err, _ = vivado.run_synthesis(
                                [wdir / f"{cfg.top_module}.v"] + extra_sources,
                                cfg.top_module, self.cfg, wdir,
                                promotions=self.taxonomy.promotions())
                            if ok:
                                winner.verilog = fixed
                                wm = vivado.full_metrics(wdir)
                                wm.sim_passed = True

            # ---- evaluation ----
            ladder_summary = "\n".join(
                f"- {c.mutation}: rungs={c.ladder_rungs_passed} "
                f"{'ALIVE' if c.alive else 'dead: ' + c.fail_reason[:80]}"
                for c in cands)
            vnotes = "\n".join(vivado.message_ids_in(wdir)[:10])
            ev = self.evaluator.evaluate(it, contract_md, ladder_summary, wm,
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
                                 **wm.to_dict()})

            # ---- restart mechanism ----
            if (ev.recommendation == "RESTART"
                    and stall >= cfg.stall_restart_threshold
                    and replans < cfg.max_replans
                    and self.budget.allow_replan()):
                replans += 1
                tried = "\n".join(
                    f"iter {d['iteration']}: {d.get('recommendation')} "
                    f"LUTs={d.get('lut_used')}"
                    for d in state.read_designs()[-8:])
                plan = self.planner.restart_plan(contract_md, stall, tried,
                                                 best_m, self.budget)
                state.write_plan(plan)
                best_v_working = original     # restart from baseline
                best_v = best_v_working if not improved else best_v
                stall, knobs_tried = 0, False
                print(f"[restart {replans}/{cfg.max_replans}] new direction planned")

        # ---- finish ----
        self._snapshot(phase="DONE", best_iteration=best_iter)
        best_path = state.run_dir / f"{cfg.top_module}_best.v"
        best_path.write_text(best_v)
        summary = {"status": "done", "best_iteration": best_iter,
                   "best_metrics": best_m.to_dict(),
                   "baseline_metrics": baseline.to_dict(),
                   "run_dir": str(state.run_dir)}
        (state.run_dir / "run_summary.json").write_text(
            json.dumps(summary, indent=2, default=str))
        print(f"\nDONE — best from iter {best_iter}: LUTs={best_m.lut_used} "
              f"FFs={best_m.ff_used} WNS={best_m.wns_ns}")
        return summary

    # ------------------------------------------------------------------ helpers
    def _full_flow(self, sources: list[Path], tb: Path | None, top: str,
                   work: Path) -> VivadoMetrics:
        m = VivadoMetrics()
        if tb:
            passed, err, _ = vivado.xsim_run(sources, tb, f"{top}_tb",
                                             self.cfg, work)
            self.budget.charge_vivado(vivado.vivado_seconds())
            m.sim_passed, m.sim_error = passed, err
            if not passed:
                return m
        else:
            m.sim_passed = True
        ok, err, _ = vivado.run_synthesis(sources, top, self.cfg, work,
                                          promotions=self.taxonomy.promotions())
        self.budget.charge_vivado(vivado.vivado_seconds())
        if not ok:
            m.synth_error = err
            return m
        m2 = vivado.full_metrics(work)
        m2.sim_passed = m.sim_passed
        return m2

    def _fix_loop(self, verilog: str, m: VivadoMetrics, tb: Path | None,
                  vfile: Path, work: Path,
                  extra: list[Path]) -> tuple[str, VivadoMetrics]:
        previous: list[str] = []
        for _ in range(self.cfg.max_fix_attempts):
            if m.sim_passed:
                break
            err = m.sim_error or m.synth_error or "unknown"
            ids = extract_message_ids(err)
            diag = "\n".join(self.taxonomy.repair_instruction(i)
                             for i in ids) or "(no message IDs found)"
            verilog = self.generator.fix(verilog, diag, err,
                                         tb.read_text()[:1500] if tb else "",
                                         previous, self.budget)
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
        """Interface-only contract from an existing design (optimize mode)."""
        import re
        ports: list[Port] = []
        for m in re.finditer(
                r"\b(input|output|inout)\s+(?:wire|reg)?\s*"
                r"(?:\[(\d+)\s*:\s*0\])?\s*(\w+)", verilog):
            direction, hi, name = m.group(1), m.group(2), m.group(3)
            ports.append(Port(name=name, direction=direction,
                              width=(int(hi) + 1) if hi else 1))
        return ModuleSpec(name=top, behavior="(existing design under optimisation)",
                          ports=ports, latency=0, reset=ResetSpec())
