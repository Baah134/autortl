"""Prompt templates — three roles, three views of the world, plus the doctor."""

LATENCY_AUTHORITY = """For optimization and review, declared_latency.known/cycles in immutable run facts
describe the current top module. Require a numeric '// @latency N' annotation
only when declared_latency.known=true, matching its authoritative cycles value.
When declared_latency.known=false, numeric top latency is UNKNOWN, not zero:
missing top annotation is neither FAIL nor INVESTIGATE and must not block ACCEPT.
Child typed-module latency metadata does not create a numeric annotation
requirement for an arbitrary aggregate wrapper. Any proven wrapper inheritance
must already appear in authoritative top latency evidence; do not infer it.
Preserve all defined cycle behavior, typed latency semantics and minimum transfer
age, registered outputs, handshakes and reset behavior. Unknown annotation
metadata never permits changing behavior or weakening deterministic gates."""

PLANNER_SYSTEM = """You are an FPGA design strategist. You plan architecture; you never write Verilog.
Think in resource trade-offs (LUT/FF/DSP48/BRAM), timing (pipeline depth, logic
levels, fanout) and Xilinx 7-series primitives. Output plain markdown, concrete
and specific.\n""" + LATENCY_AUTHORITY

GENERATOR_SYSTEM = """You are an expert FPGA engineer writing synthesisable Verilog for Xilinx
7-series in Vivado. Output ONLY the complete module inside one ```verilog fence.
Rules: exact interface from the contract (name, ports, widths, signedness, packed
shape and public parameters). Reset kind, polarity and priority match the contract. No initial blocks. Every reg in a combinational always @(*) assigned in
all branches (defaults at the top). When the contract provides a fixed numeric
latency N, include a '// @latency N' header matching it and preserve its cycle
behavior. When numeric latency is UNKNOWN, do not invent an @latency annotation
or assume zero cycles: preserve the frozen source's exact observable cycles,
including registered outputs. An annotation alone is not behavioral proof.
Write behavioral RTL that Vivado infers to device primitives; never instantiate
primitives such as CARRY4, LUT6, FDRE, DSP48E1, SRL16E or RAMB18E1 by name.
Verification simulates behavioral RTL without the UNISIM library, so an
instantiated primitive fails elaboration.\n""" + LATENCY_AUTHORITY

EVALUATOR_SYSTEM = """You are an FPGA design reviewer grading against a fixed contract. You are
not here to help or suggest; you enforce the contract line by line. Mark
unverifiable criteria INVESTIGATE. Never rubber-stamp. Use the exact output
format requested.\n""" + LATENCY_AUTHORITY

DOCTOR_SYSTEM = """You are a timing-closure specialist for Xilinx 7-series. Given a diagnosed
category and a surgical instruction, produce a minimally-changed module that
implements exactly that change. Output ONLY the module in one ```verilog fence.
Infer device primitives from behavioral RTL; never instantiate CARRY4, LUT6,
FDRE, DSP48E1 or other UNISIM primitives by name (verification simulates
behavioral RTL only)."""

SPEC_PROMPT = """Produce a design_spec JSON for this request.

**Request:** {intent}
**Target:** {target_part} @ {target_freq_mhz} MHz. **Objective:** {objective}

Output ONLY JSON matching this schema (no commentary):
{{"top_name": str,
  "modules": [{{"name": str, "behavior": str-one-paragraph,
     "ports": [{{"name": str, "direction": "input|output", "width": int,
                "signed": false, "packed_dimensions": null,
                "clock_domain": "clk", "protocol": "none|valid_ready"}}],
     "latency": int, "compare_mode": "fixed_latency|scoreboard",
     "reset": {{"signal": "rst", "kind": "sync", "active_high": true,
               "duration_cycles": 5}},
     "clock_domains": ["clk"], "parameters": {{}},
     "examples": [{{"inputs": {{}}, "expected": {{}}, "after_cycles": int}}] }}],
  "connections": [{{"src_module": str, "src_port": str,
                    "dst_module": str, "dst_port": str}}],
  "external_ports": [ports of the top level] }}

Port signed is an optional boolean (default false). packed_dimensions is optional
null (legacy descending [width-1:0], scalar for width 1) or a list of [left,right]
integer bound pairs, for example [[0,7]] or [[1,0],[3,0]]. Preserve direction and
shape; the product of dimension sizes must equal width. Parameters are public
integer defaults, not internal localparams. Do not emit interface_signature;
the harness derives that immutable metadata from existing source.
Typed build modules require a known numeric latency; latency_known, if supplied,
must be true. An absent annotation in an existing optimization source is a
separate case and must never be interpreted as zero cycles.
Every module MUST include 2-3 concrete examples. Keep modules under ~60 lines
of eventual Verilog each; split anything bigger.
Each example runs the Python reference for after_cycles steps inside a fixed
sandbox budget, so keep every after_cycles at or below 2000. For long-period
designs (for example a UART bit lasting hundreds of cycles), make each example
check an early part of the behavior, such as the start bit and the first data
bits, rather than a whole frame; full-length behavior is checked by the
generated testbench and any independent testbench.
Structural rules the harness checks before any generation:
- top_name names the top wrapper the harness generates mechanically. It must be
  a valid identifier that differs from every module name: a request for a single
  module `foo` has modules [{{"name": "foo", ...}}] and top_name "foo_top".
- Module names are unique. Every module input is driven by exactly one
  connection or is an external port with the same name, direction, width,
  protocol and signedness. Each external output is driven by exactly one
  module output of that name. Connected ports agree in width, signedness,
  shape, protocol and clock domain."""

CONTRACT_PROPOSAL = """Propose a CONTRACT: a testable checklist of success for this run.
Mode: {mode}. Objective: {objective}. Target: {target_part} @ {target_freq_mhz} MHz.
Baseline: sim={sim_status} LUTs={lut_used} FFs={ff_used} WNS={wns_ns}ns
{device_budget}

{design_context}

The attached authoritative harness facts define tool versions, sources, provided
verification, constraints and baseline measurements. Use their actual values.
Keep a concise checklist of the fixed hard gates and a separate advisory
optimization goal. Do not invent mandatory savings/slack targets, testbench names,
versions, comparison thresholds, timing corners or code-style quotas. Preserve
all observable baseline behavior. Include no requirement to modify the harness.
Output 5-8 criteria in exactly this markdown structure:
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
Review using the attached authoritative harness facts. They are fixed and already
implemented; do not demand extra tool settings, board constraints, corner values,
new tests or naming/style conventions. Unknown facts must stay unknown. Reject
criteria that contradict these facts or make an advisory improvement goal a
mandatory success threshold. A correct completed experiment may find no gain.
Output "ACCEPT: ..." if testable as written, else bullet criticisms with rewrites.

{contract}"""

CONTRACT_REFINE = """Revise the contract to address this feedback. Same format. Every criterion
objectively testable under the attached immutable harness facts. Do not invent
new environment requirements or guaranteed savings. Output only the revised
checklist, without rewriting or copying the authoritative facts.
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
# Verified incumbent measurements (may describe a different source from the generation seed)
LUTs={lut_used} FFs={ff_used} WNS={wns_ns}ns DSP={dsp_used} BRAM={bram_used}
Register-to-register WNS (advisory; excludes I/O pad delay): {reg2reg}
# Actual generation seed (write instructions for this source)
```verilog
{generation_seed}
```
Baseline source facts remain immutable verification context. The source above is
the code the generator will modify; incumbent measurements are not measurements
of this seed unless independently established by retained evidence.
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
2-4 sentences naming the exact code pattern to change. The generator also receives
the immutable harness facts, fixed contract and frozen compilation boundary.
Respect explicit unspecified cases in supplied build specifications; do not invent
extra behavioral requirements. Use retained trial evidence to avoid repeating an
unchanged failed experiment. Prior proposal outcomes are advisory observations,
not new contract requirements. Name a concrete change from an already tried
proposal when appropriate; identical RTL remains valid for different physical
settings, and a new source hash alone does not establish an improvement."""

RESTART_PLAN = """The loop has stalled ({stall_count} iterations without improvement).
# Contract
{contract}
# Verified incumbent measurements (preserved across restart)
LUTs={lut_used} FFs={ff_used} WNS={wns_ns}ns
# Original generation seed for restart (write instructions for this source)
```verilog
{generation_seed}
```
The original seed can differ from the verified incumbent. Its measurements must
not be inferred from the incumbent measurements or advisory history.
# Already tried on this line (do NOT reuse or refine any of these)
{tried}

Propose a fundamentally different architectural direction. The current best is
preserved, so be radical. Output the standard PLAN format."""

GENERATE = """{skills}

**Contract for module {name}:**
Behavior: {behavior}
Ports: {ports_table}
Public parameter defaults (preserve names/order/defaults): {parameters}
Frozen source interface signature: {interface_signature}
The signature is authoritative when present: retain public parameter types/default
expressions and symbolic port dimensions, not just their resolved default widths.
Internal localparams may change only when the external contract remains identical.
Latency: {latency}. Reset: {reset_desc}.

**Approach for this candidate:** {mutation}

**Instruction:** {instruction}

**Current code (modify this):**
```verilog
{verilog}
```
Return the complete module in one ```verilog fence. {latency_header}"""

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
Use the attached candidate source, complete current and previous-best metrics
and immutable run facts. Judge improvement from those metrics and the recorded
improvement_kind. A verified candidate with timing_met=true, nonnegative setup
and hold may replace a known timing-infeasible previous best even if area/power
is equal or higher: timing_recovery is feasibility recovery, not resource savings.
Unknown or contradictory timing evidence cannot establish recovery. Once both
incumbent and candidate are timing-feasible, require strict improvement of the
chosen objective. Never reject a valid timing recovery solely for higher area
or power. Extra savings or slack margins are advisory goals, not mandatory gates. Do not invent missing
measurements or change the provided testbench, latency, constraints or tools.
Use authoritative declared_latency for the current top's annotation requirement.
If known=false, do not reject or demand investigation solely because the top has
no @latency comment. A typed child's latency does not declare aggregate top latency.
ACCEPT requires zero failed mandatory criteria; otherwise REJECT.

# Contract
{contract}
# Ladder results (authoritative)
{ladder}
# Metrics
sim={sim_status} LUTs={lut_used} FFs={ff_used} WNS={wns_ns}ns timing_met={timing_met}
Register-to-register WNS (advisory; excludes I/O pad delay, not a gate): {reg2reg}
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
Public parameter defaults: {parameters}
Inputs and outputs remain masked nonnegative bit patterns even for signed ports.
For signed arithmetic, explicitly interpret two's-complement operands at their
specified widths, then mask outputs. Signed declarations do not change this API.
Required API scaffold (syntax only, not a complete behavioral implementation):
```python
def init():
    return dict()

def step(state, inputs):
    outputs = dict()
    return state, outputs
```
Replace the empty state/output placeholders with the specified behavior; fill
outputs with every named data output below. Use unannotated function signatures.
Restricted Python execution, not general Python:
Allowed builtins: {safe_builtins}
Allowed methods: {safe_methods}
Use integer arithmetic/bit operations, assignments, if/else and bounded loops.
Helper functions are allowed. No imports, classes, try/except, raise, lambda,
f-strings, list/dict/set comprehensions, floats, decorators or default arguments.
Generator expressions are supported. Do not use private names starting with '_'.
Use literal port names, for example inputs.get("port_name", 0), replacing the
placeholder with a declared name. str() and .format() are unsupported; do not
construct port names with string formatting. No file/network/system access.
Comparison mode: {compare_mode}. Declared RTL latency: {latency}. Reset: {reset_desc}.
Output keys must be exactly these data outputs: {data_outputs}; do not return
valid/ready control outputs. Values are masked plain integers. The clock edge
is implicit; do not read clk. Handle reset input explicitly when supplied;
init() must represent reset state. Generated comparisons begin with asserted
reset steps, followed by deasserted reset and data stimulus. Spec examples may
supply controls explicitly; use suitable inactive defaults for omitted controls.
For fixed_latency, model one logical input/state transition per step and return
its behavioral result. The testbench handles the declared pipeline delay; do
not add a separate pipeline-delay queue in the Python model.
For scoreboard, each non-reset step is ONE ACCEPTED input transaction: return
its eventual output payload. Do not simulate buffer occupancy, valid/ready
scheduling, bubbles or backpressure; the testbench independently schedules and
checks those RTL behaviors. Supplied handshake inputs are 1 for accepted
transactions and 0 during reset. Output ONLY python in one ```python fence."""
