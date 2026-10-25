"""Planner / Generator / Evaluator / TimingDoctor — isolated views, one client."""
from __future__ import annotations
import re
import json
from dataclasses import dataclass
from pathlib import Path

from . import prompts
from .spec import ModuleSpec, DesignSpec, port_declaration
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
    return "\n".join(f"  {port_declaration(p, include_direction=True)} "
                     f"(clock={p.clock_domain}, protocol={p.protocol})"
                     for p in spec.ports)


def evidence_prompt(role, prompt, include_candidate=False, include_proposals=False):
    facts = getattr(role, "run_context", "")
    candidate = getattr(role, "candidate_context", "")
    if facts:
        prompt += "\n\n# AUTHORITATIVE HARNESS FACTS (immutable)\n" + facts
    if candidate and include_candidate:
        prompt += "\n\n# CURRENT CANDIDATE EVIDENCE (immutable)\n" + candidate
    if include_proposals and getattr(role, "proposal_context", ""):
        prompt += "\n\n# PRIOR PROPOSAL OUTCOMES (advisory)\n" + role.proposal_context
    return prompt


def role_system(instruction):
    """Every role receives one copy of fixed-contract conventions."""
    return instruction + "\n" + conventions()


class Planner:
    def make_spec(self, intent: str, cfg, budget) -> str:
        p = prompts.SPEC_PROMPT.format(intent=intent, target_part=cfg.target_part,
                                       target_freq_mhz=cfg.target_freq_mhz,
                                       objective=cfg.objective)
        return ask("planner", evidence_prompt(self, p), system=role_system(prompts.PLANNER_SYSTEM),
                   budget=budget)

    def propose_contract(self, mode, cfg, baseline: VivadoMetrics,
                         design_context: str, budget) -> str:
        p = prompts.CONTRACT_PROPOSAL.format(
            mode=mode, objective=cfg.objective, target_part=cfg.target_part,
            target_freq_mhz=cfg.target_freq_mhz,
            sim_status="PASSED" if baseline.sim_passed else "FAILED",
            lut_used=baseline.lut_used, ff_used=baseline.ff_used,
            wns_ns=baseline.wns_ns, design_context=design_context,
            device_budget=budget_text(cfg.target_part))
        return ask("planner", evidence_prompt(self, p), system=role_system(prompts.PLANNER_SYSTEM), budget=budget)

    def refine_contract(self, contract, feedback, budget) -> str:
        p = prompts.CONTRACT_REFINE.format(feedback=feedback, contract=contract)
        return ask("planner", evidence_prompt(self, p), system=role_system(prompts.PLANNER_SYSTEM), budget=budget)

    def plan(self, iteration, contract, progress, evaluations, best: VivadoMetrics,
             signals, budget, target_part="", advisor="", generation_seed=None) -> str:
        p = prompts.PLAN.format(
            iteration=iteration, contract=contract, progress=progress,
            generation_seed=generation_seed if generation_seed is not None else "(not supplied)",
            planning_skill=inject(["fpga-methodology"]),
            device_budget=budget_text(target_part) or "(unknown part)",
            advisor=advisor or "(no advisor output available)",
            evaluations="\n---\n".join(evaluations) or "(none)",
            lut_used=best.lut_used, ff_used=best.ff_used, wns_ns=best.wns_ns,
            dsp_used=best.dsp_used, bram_used=best.bram_used,
            signals="\n".join(f"- {s.kind}: {s.detail}" for s in signals) or "(none)")
        return ask("planner", evidence_prompt(self, p, include_proposals=True), system=role_system(prompts.PLANNER_SYSTEM), budget=budget)

    def restart_plan(self, contract, stall_count, tried, best: VivadoMetrics,
                     budget, generation_seed=None) -> str:
        p = prompts.RESTART_PLAN.format(contract=contract, stall_count=stall_count,
                                        tried=tried, lut_used=best.lut_used,
                                        ff_used=best.ff_used, wns_ns=best.wns_ns,
                                        generation_seed=generation_seed if generation_seed is not None else "(not supplied)")
        return ask("planner", evidence_prompt(self, p, include_proposals=True), system=role_system(prompts.PLANNER_SYSTEM), budget=budget)


class Generator:
    def generate(self, module: ModuleSpec, verilog: str, instruction: str,
                 mutation_text: str, budget) -> str:
        skills = inject(select_for_module(module))
        r = module.reset
        latency = (f"{module.latency} cycles (fixed numeric contract)" if module.latency_known else
                   "UNKNOWN numeric latency: preserve the exact frozen source's observable cycles; "
                   "an absent annotation does not mean zero cycles")
        latency_header = (f"Include a '// @latency {module.latency}' header matching the fixed numeric contract."
                          if module.latency_known else
                          "Do not invent an @latency header or infer zero latency from its absence. "
                          "Preserve exact source cycle behavior, including registered outputs.")
        p = prompts.GENERATE.format(
            skills=skills, name=module.name, behavior=module.behavior,
            ports_table=_ports_table(module), latency=latency, latency_header=latency_header,
            parameters=json.dumps(module.parameters),
            interface_signature=json.dumps(module.interface_signature, sort_keys=True),
            reset_desc=f"{r.kind}, active_{'high' if r.active_high else 'low'} '{r.signal}'",
            mutation=mutation_text, instruction=instruction, verilog=verilog)
        resp = ask("generator", evidence_prompt(self, p, include_proposals=True), system=role_system(prompts.GENERATOR_SYSTEM),
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
        resp = ask("generator", evidence_prompt(self, p), system=role_system(prompts.GENERATOR_SYSTEM),
                   budget=budget)
        return generated_rtl(resp)

    def golden_model(self, module: ModuleSpec, budget, feedback: str = "") -> str:
        from .golden_worker import SAFE_BUILTINS, SAFE_METHODS
        p = prompts.GOLDEN_MODEL.format(behavior=module.behavior,
                                        safe_builtins=", ".join(sorted(SAFE_BUILTINS)),
                                        safe_methods=", ".join(sorted(SAFE_METHODS)),
                                        ports_table=_ports_table(module),
                                        parameters=json.dumps(module.parameters),
                                        compare_mode=module.compare_mode, latency=module.latency,
                                        reset_desc=f"{module.reset.kind}, active_{'high' if module.reset.active_high else 'low'} '{module.reset.signal}'",
                                        data_outputs=json.dumps([p.name for p in module.ports if p.direction == "output" and p.protocol == "none"]))
        if feedback:
            p += "\n\nThe previous Python reference failed validation. Repair this specific failure " + str(feedback)[:1800]
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
        p = re.search(r"Passed:\s*(\d+)\s+of\s+(\d+)", raw, re.IGNORECASE)
        f = re.search(r"Failed:\s*(\d+)", raw, re.IGNORECASE)
        passed, failed = int(p.group(1)) if p else 0, int(f.group(1)) if f else 1
        consistent = p and f and passed > 0 and passed + failed == int(p.group(2))
        unresolved = re.search(r"(?m)^\s*-\s+.*?:\s*(?:FAIL|INVESTIGATE)\b", raw, re.IGNORECASE)
        recommendation = rec.group(1).upper() if rec else "REJECT"
        if not consistent or unresolved or (recommendation == "ACCEPT" and failed):
            recommendation = "REJECT"
            failed = max(failed, 1)
        return Evaluation(raw, recommendation, passed, failed)


class Evaluator:
    def review_contract(self, contract: str, budget) -> str:
        return ask("evaluator", evidence_prompt(self, prompts.CONTRACT_REVIEW.format(contract=contract)),
                   system=role_system(prompts.EVALUATOR_SYSTEM), budget=budget)

    def evaluate(self, iteration, contract, ladder_summary, m: VivadoMetrics,
                 vivado_notes, stall_count, restart_threshold, budget) -> Evaluation:
        p = prompts.EVALUATE.format(
            iteration=iteration, contract=contract, ladder=ladder_summary,
            sim_status="PASSED" if m.sim_passed else "FAILED",
            lut_used=m.lut_used, ff_used=m.ff_used, wns_ns=m.wns_ns,
            timing_met=m.timing_met, dsp_used=m.dsp_used, bram_used=m.bram_used,
            vivado_notes=vivado_notes or "(none)", stall_count=stall_count,
            restart_threshold=restart_threshold)
        return Evaluation.parse(ask("evaluator", evidence_prompt(self, p, include_candidate=True), system=role_system(prompts.EVALUATOR_SYSTEM),
                                    budget=budget))


class TimingDoctor:
    """Timing repair role; worker timeout is bounded, max_turns is advisory."""
    def surgery(self, verilog: str, instruction: str, path_snippet: str,
                budget) -> str:
        skills = inject(select_for_timing())
        p = (f"{skills}\n\n**Surgical instruction:** {instruction}\n\n"
             f"**Failing timing path:**\n```\n{path_snippet[:1200]}\n```\n\n"
             f"**Current module:**\n```verilog\n{verilog}\n```")
        resp = ask("timing_doctor", evidence_prompt(self, p), system=role_system(prompts.DOCTOR_SYSTEM),
                   budget=budget, max_turns=3)
        return generated_rtl(resp)
