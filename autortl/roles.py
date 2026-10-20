"""Planner / Generator / Evaluator / TimingDoctor — isolated views, one client."""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

from . import prompts
from .spec import ModuleSpec, DesignSpec
from .skill_loader import (conventions, select_for_module, select_for_timing, inject, load_skill)
from .device import budget_text
from .report_parser import VivadoMetrics
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.client import ask, extract_verilog


def generated_rtl(response: str) -> str:
    """Generated sources use the harness simulation unit unless explicit."""
    source = extract_verilog(response)
    uncommented = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
    if not re.search(r"(?m)^\s*`timescale\b", uncommented):
        source = "`timescale 1ns/1ps\n" + source
    return source


def _ports_table(spec: ModuleSpec) -> str:
    return "\n".join(f"  {p.direction:6} [{p.width-1}:0] {p.name} "
                     f"(clock={p.clock_domain}, protocol={p.protocol})"
                     for p in spec.ports)


class Planner:
    def make_spec(self, intent: str, cfg, budget) -> str:
        p = prompts.SPEC_PROMPT.format(intent=intent, target_part=cfg.target_part,
                                       target_freq_mhz=cfg.target_freq_mhz,
                                       objective=cfg.objective)
        return ask("planner", p, system=prompts.PLANNER_SYSTEM + "\n" + conventions(),
                   budget=budget)

    def propose_contract(self, mode, cfg, baseline: VivadoMetrics,
                         design_context: str, budget) -> str:
        p = prompts.CONTRACT_PROPOSAL.format(
            mode=mode, objective=cfg.objective, target_part=cfg.target_part,
            target_freq_mhz=cfg.target_freq_mhz,
            sim_status="PASSED" if baseline.sim_passed else "FAILED",
            lut_used=baseline.lut_used, ff_used=baseline.ff_used,
            wns_ns=baseline.wns_ns, design_context=design_context[:6000],
            device_budget=budget_text(cfg.target_part))
        return ask("planner", p, system=prompts.PLANNER_SYSTEM, budget=budget)

    def refine_contract(self, contract, feedback, budget) -> str:
        p = prompts.CONTRACT_REFINE.format(feedback=feedback, contract=contract)
        return ask("planner", p, system=prompts.PLANNER_SYSTEM, budget=budget)

    def plan(self, iteration, contract, progress, evaluations, best: VivadoMetrics,
             signals, budget, target_part="", advisor="") -> str:
        p = prompts.PLAN.format(
            iteration=iteration, contract=contract, progress=progress,
            planning_skill=inject(["fpga-methodology"]),
            device_budget=budget_text(target_part) or "(unknown part)",
            advisor=advisor or "(no advisor output available)",
            evaluations="\n---\n".join(evaluations) or "(none)",
            lut_used=best.lut_used, ff_used=best.ff_used, wns_ns=best.wns_ns,
            dsp_used=best.dsp_used, bram_used=best.bram_used,
            signals="\n".join(f"- {s.kind}: {s.detail}" for s in signals) or "(none)")
        return ask("planner", p, system=prompts.PLANNER_SYSTEM, budget=budget)

    def restart_plan(self, contract, stall_count, tried, best: VivadoMetrics,
                     budget) -> str:
        p = prompts.RESTART_PLAN.format(contract=contract, stall_count=stall_count,
                                        tried=tried, lut_used=best.lut_used,
                                        ff_used=best.ff_used, wns_ns=best.wns_ns)
        return ask("planner", p, system=prompts.PLANNER_SYSTEM, budget=budget)


class Generator:
    def generate(self, module: ModuleSpec, verilog: str, instruction: str,
                 mutation_text: str, budget) -> str:
        skills = inject(select_for_module(module))
        r = module.reset
        p = prompts.GENERATE.format(
            skills=skills, name=module.name, behavior=module.behavior,
            ports_table=_ports_table(module), latency=module.latency,
            reset_desc=f"{r.kind}, active_{'high' if r.active_high else 'low'} '{r.signal}'",
            mutation=mutation_text, instruction=instruction, verilog=verilog)
        resp = ask("generator", p, system=prompts.GENERATOR_SYSTEM + "\n" + conventions(),
                   budget=budget)
        return generated_rtl(resp)

    def fix(self, verilog: str, diagnosis: str, error: str, tb_excerpt: str,
            previous: list[str], budget) -> str:
        prev = ""
        if previous:
            prev = ("\n**Previous fix attempts that STILL failed (do not repeat "
                    "these approaches):**\n" +
                    "\n".join(f"- attempt {i+1}: {e[:200]}" for i, e in enumerate(previous)))
        p = prompts.FIX.format(diagnosis=diagnosis, error=error[:1500],
                               verilog=verilog, tb_excerpt=tb_excerpt[:2000],
                               previous_attempts=prev)
        resp = ask("generator", p, system=prompts.GENERATOR_SYSTEM + "\n" + conventions(),
                   budget=budget)
        return generated_rtl(resp)

    def golden_model(self, module: ModuleSpec, budget) -> str:
        p = prompts.GOLDEN_MODEL.format(behavior=module.behavior,
                                        ports_table=_ports_table(module))
        resp = ask("generator", p, system=conventions(), budget=budget)
        m = re.search(r"```python\s*\n(.*?)```", resp, re.DOTALL)
        return m.group(1).strip() if m else resp.strip()


@dataclass
class Evaluation:
    raw: str
    recommendation: str
    passed: int
    failed: int

    @staticmethod
    def parse(raw: str) -> "Evaluation":
        rec = re.search(r"##\s*Recommendation\s*\n\s*(ACCEPT|REJECT|RESTART)",
                        raw, re.IGNORECASE)
        p = re.search(r"Passed:\s*(\d+)", raw)
        f = re.search(r"Failed:\s*(\d+)", raw)
        return Evaluation(raw, rec.group(1).upper() if rec else "REJECT",
                          int(p.group(1)) if p else 0, int(f.group(1)) if f else 0)


class Evaluator:
    def review_contract(self, contract: str, budget) -> str:
        return ask("evaluator", prompts.CONTRACT_REVIEW.format(contract=contract),
                   system=prompts.EVALUATOR_SYSTEM, budget=budget)

    def evaluate(self, iteration, contract, ladder_summary, m: VivadoMetrics,
                 vivado_notes, stall_count, restart_threshold, budget) -> Evaluation:
        p = prompts.EVALUATE.format(
            iteration=iteration, contract=contract, ladder=ladder_summary,
            sim_status="PASSED" if m.sim_passed else "FAILED",
            lut_used=m.lut_used, ff_used=m.ff_used, wns_ns=m.wns_ns,
            timing_met=m.timing_met, dsp_used=m.dsp_used, bram_used=m.bram_used,
            vivado_notes=vivado_notes or "(none)", stall_count=stall_count,
            restart_threshold=restart_threshold)
        return Evaluation.parse(ask("evaluator", p, system=prompts.EVALUATOR_SYSTEM,
                                    budget=budget))


class TimingDoctor:
    """The one role with bounded agentic latitude (max_turns=3)."""
    def surgery(self, verilog: str, instruction: str, path_snippet: str,
                budget) -> str:
        skills = inject(select_for_timing())
        p = (f"{skills}\n\n**Surgical instruction:** {instruction}\n\n"
             f"**Failing timing path:**\n```\n{path_snippet[:1200]}\n```\n\n"
             f"**Current module:**\n```verilog\n{verilog}\n```")
        resp = ask("timing_doctor", p, system=prompts.DOCTOR_SYSTEM + "\n" + conventions(),
                   budget=budget, max_turns=3)
        return generated_rtl(resp)
