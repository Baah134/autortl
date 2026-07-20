"""Prompt templates — three roles, three views of the world, plus the doctor."""

PLANNER_SYSTEM = """You are an FPGA design strategist. You plan architecture; you never write Verilog.
Think in resource trade-offs (LUT/FF/DSP48/BRAM), timing (pipeline depth, logic
levels, fanout) and Xilinx 7-series primitives. Output plain markdown, concrete
and specific."""

GENERATOR_SYSTEM = """You are an expert FPGA engineer writing synthesisable Verilog for Xilinx
7-series in Vivado. Output ONLY the complete module inside one ```verilog fence.
Rules: exact interface from the contract (name, ports, widths). Synchronous
resets. No initial blocks. Every reg in a combinational always @(*) assigned in
all branches (defaults at the top). Declare pipeline depth with a '// @latency N'
header comment matching the contract latency — the spec is law; if you cannot
meet the declared latency, still match it rather than silently changing it."""

EVALUATOR_SYSTEM = """You are an FPGA design reviewer grading against a fixed contract. You are
not here to help or suggest; you enforce the contract line by line. Mark
unverifiable criteria INVESTIGATE. Never rubber-stamp. Use the exact output
format requested."""

DOCTOR_SYSTEM = """You are a timing-closure specialist for Xilinx 7-series. Given a diagnosed
category and a surgical instruction, produce a minimally-changed module that
implements exactly that change. Output ONLY the module in one ```verilog fence."""

SPEC_PROMPT = """Produce a design_spec JSON for this request.

**Request:** {intent}
**Target:** {target_part} @ {target_freq_mhz} MHz. **Objective:** {objective}

Output ONLY JSON matching this schema (no commentary):
{{"top_name": str,
  "modules": [{{"name": str, "behavior": str-one-paragraph,
     "ports": [{{"name": str, "direction": "input|output", "width": int,
                "clock_domain": "clk", "protocol": "none|valid_ready"}}],
     "latency": int, "compare_mode": "fixed_latency|scoreboard",
     "reset": {{"signal": "rst", "kind": "sync", "active_high": true,
               "duration_cycles": 5}},
     "clock_domains": ["clk"], "parameters": {{}},
     "examples": [{{"inputs": {{}}, "expected": {{}}, "after_cycles": int}}] }}],
  "connections": [{{"src_module": str, "src_port": str,
                    "dst_module": str, "dst_port": str}}],
  "external_ports": [ports of the top level] }}

Every module MUST include 2-3 concrete examples. Keep modules under ~60 lines
of eventual Verilog each; split anything bigger."""

CONTRACT_PROPOSAL = """Propose a CONTRACT: a testable checklist of success for this run.
Mode: {mode}. Objective: {objective}. Target: {target_part} @ {target_freq_mhz} MHz.
Baseline: sim={sim_status} LUTs={lut_used} FFs={ff_used} WNS={wns_ns}ns
{device_budget}

{design_context}

Output 8-15 criteria in exactly this markdown structure:
# CONTRACT
## Resource targets
- [ ] ...
## Timing targets
- [ ] ...
## Correctness
- [ ] ...
## Code quality
- [ ] ...
## Definition of done
One paragraph.
Every criterion must be verifiable from Vivado output or the code alone."""

CONTRACT_REVIEW = """Review this contract for testability. Push back on vague terms, missing
thresholds, and unverifiable judgment. Under 200 words.
Output "ACCEPT: ..." if testable as written, else bullet criticisms with rewrites.

{contract}"""

CONTRACT_REFINE = """Revise the contract to address this feedback. Same format. Every criterion
objectively testable.
Feedback:
{feedback}
Original:
{contract}"""

PLAN = """Plan iteration {iteration} of an FPGA optimisation loop.
{planning_skill}
# Device budget
{device_budget}
# Contract
{contract}
# Progress (recent)
{progress}
# Recent evaluations
{evaluations}
# Current best
LUTs={lut_used} FFs={ff_used} WNS={wns_ns}ns DSP={dsp_used} BRAM={bram_used}
# Vivado advisor (advisory only | strong evidence from the tool that will judge)
{advisor}
# Watchdog signals
{signals}

Output exactly:
# PLAN — iteration {iteration}
## Current state assessment
one paragraph
## Hypothesis
one sentence
## Instruction for generator
2-4 sentences naming the exact code pattern to change. The generator sees ONLY
this instruction and the current code."""

RESTART_PLAN = """The loop has stalled ({stall_count} iterations without improvement).
# Contract
{contract}
# Current best
LUTs={lut_used} FFs={ff_used} WNS={wns_ns}ns
# Already tried on this line (do NOT reuse or refine any of these)
{tried}

Propose a fundamentally different architectural direction. The current best is
preserved, so be radical. Output the standard PLAN format."""

GENERATE = """{skills}

**Contract for module {name}:**
Behavior: {behavior}
Ports: {ports_table}
Latency: {latency} cycles. Reset: {reset_desc}.

**Approach for this candidate:** {mutation}

**Instruction:** {instruction}

**Current code (modify this):**
```verilog
{verilog}
```
Return the complete module in one ```verilog fence with a '// @latency {latency}' header."""

FIX = """The Verilog failed verification.

**Diagnosed errors:**
{diagnosis}

**Raw error excerpt:**
```
{error}
```

**Failing code:**
```verilog
{verilog}
```

**Testbench interface for reference (do NOT modify, shown as text):**
```text
{tb_excerpt}
```
{previous_attempts}
Return the complete fixed module in one ```verilog fence. Interface must match
the contract exactly."""

EVALUATE = """Grade this design against the contract. Deterministic ladder results are
authoritative for correctness; you rule only on the subjective residue.

# Contract
{contract}
# Ladder results (authoritative)
{ladder}
# Metrics
sim={sim_status} LUTs={lut_used} FFs={ff_used} WNS={wns_ns}ns timing_met={timing_met}
DSP={dsp_used} BRAM={bram_used}
# Vivado notes
{vivado_notes}
# Stall count
{stall_count}

Output exactly:
# EVALUATION — iteration {iteration}
## Contract check
- <criterion>: PASS/FAIL/INVESTIGATE — reason
## Summary
- Passed: X of Y
- Failed: X of Y
- Improved over previous best: YES/NO/N-A
## Recommendation
ACCEPT | REJECT | RESTART
## Reason
one paragraph. RESTART only if stall count >= {restart_threshold}."""

GOLDEN_MODEL = """Write a Python golden model for this module.
Behavior: {behavior}
Ports: {ports_table}
It must define exactly:
    def init(): return state
    def step(state, inputs: dict) -> (state, outputs: dict)
inputs/outputs keys are the port names; values are plain ints (masked to port
width). Model ONE clock cycle per step. Output ONLY python in one ```python fence."""
