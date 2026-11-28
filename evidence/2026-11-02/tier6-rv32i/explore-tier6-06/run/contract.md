# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (rv_imem, rv_decode, rv_regfile, rv_alu, rv_dmem, rv_ctrl) and the top rv32i_core, children first and top last; no frozen companion is compiled beside it. Only the top rv32i_core carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define rv32i_core. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory. Their latency fields and annotations bind nothing on their own: a child module needs no // @latency annotation, and a missing or changed child annotation is never a failed criterion (evaluator_requires_child_latency_annotation).

## Implementation flow

Mode out_of_context, fixed by the harness. Out-of-context implementation (chip_top_flow_for_soc_block): the top is a block inside a larger design, synthesized with synth_design -mode out_of_context and placed and routed without I/O buffers or package pins. clk is constrained at the target period and modeled as driven by a global clock buffer (HD.CLK_SRC). Data ports have no input or output delay and no pad delay, so they are unconstrained I/O; the routed WNS and WHS, and timing acceptance, cover the internal clocked paths only, and combinational logic between a port and its first or last register is not timed. Utilization excludes I/O buffers.

## Verification gates

The current top's numeric latency is UNKNOWN, not zero. Its missing @latency annotation is neither FAIL nor INVESTIGATE and must not block ACCEPT. Do not invent a numeric top annotation from child typed-module metadata or an arbitrary aggregate wrapper. Only authoritative current-top declared_latency.known=true creates a numeric annotation requirement. Preserve defined typed latency semantics, minimum transfer age, registered outputs, reset and cycle behavior; all deterministic checks remain mandatory. 

Use the frozen testbench unchanged. Pass static/interface and declared latency checks when a numeric declaration is known, xvlog compilation, xelab elaboration and xsim -runall. Unannotated numeric latency is UNKNOWN, not zero; an annotation alone is not independent behavioral proof. Tool stages require successful exit codes; synthesis also requires the SYNTH_COMPLETE marker. Simulation requires the exact standalone TEST PASSED verdict and rejects TEST FAILED, missing verdicts, tool errors and timeouts. Provided testbench coverage is not formal equivalence. Require valid retained routed reports and metric integrity; setup WNS >= 0 and hold WHS >= 0 are both mandatory for timing closure and for promotion, except timing_progress below. Missing or unknown evidence is not success.

## Objective and completion

First establish timing feasibility: the candidate must pass simulation and all verification/metric/receipt gates, with timing_met=true, WNS >= 0 and WHS >= 0. A candidate meeting those gates may replace a previous verified best whose known consistent timing evidence fails setup or hold, even when area or power increases or stays equal. Classify this as timing_recovery: a feasibility recovery, not resource or power savings. Unknown, missing or contradictory timing evidence does not establish a timing recovery. While the previous best is still timing-infeasible, a verified candidate that is also infeasible may replace it only with strictly better setup WNS and hold WHS not worse beyond a small tolerance. Classify this as timing_progress: progress toward closure, not closure; a timing-feasible candidate always outranks it, a feasible previous best is never replaced by an infeasible candidate, and a run whose best is still infeasible has not closed timing. Once both designs are timing-feasible, objective minimize_luts maps to (lut_used, ff_used) compared lexicographically: require strictly lower lut_used, or equal lut_used with strictly lower ff_used, than the previous verified best, under the same device, clock and constraints. Higher lut_used is never an objective improvement. When either design lacks a finite ff_used, only strictly lower lut_used counts. No minimum percentage gain or extra slack margin is imposed. Final evaluator ACCEPT with zero failed criteria and all deterministic promotion gates are required. DONE describes a completed experiment; best_iteration 0 retains the baseline and claims no accepted improvement. Only a promoted best_iteration > 0 establishes an accepted improvement; its recorded kind distinguishes timing recovery and timing progress from objective gain.

## Fixed measurement authority

The JSON below records source/testbench identities, actual device, clock, tool context, constraints and retained report hashes. Numeric metrics are the parsed structured evidence, with routed reports preferred. The candidate's retained synthesis script records actual permitted retiming or physical optimization settings; these never change behavioral obligations.

```json
{
  "baseline_metrics": {
    "bram_total": 50.0,
    "bram_used": 0.0,
    "dsp_total": 90,
    "dsp_used": 0,
    "dynamic_power_w": 0.014,
    "ff_pct": 10.471153846153847,
    "ff_total": 41600,
    "ff_used": 4356,
    "lut_pct": 10.0625,
    "lut_total": 20800,
    "lut_used": 2093,
    "reg2reg_wns_ns": 1.201,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": true,
    "total_power_w": 0.082,
    "whs_ns": 0.053,
    "wns_ns": 1.201
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\design_spec.json",
    "resolved_spec": {
      "connections": [
        {
          "dst_module": "rv_imem",
          "dst_port": "imem_raddr",
          "src_module": "rv_ctrl",
          "src_port": "imem_raddr"
        },
        {
          "dst_module": "rv_decode",
          "dst_port": "instr",
          "src_module": "rv_imem",
          "src_port": "imem_rdata"
        },
        {
          "dst_module": "rv_regfile",
          "dst_port": "raddr1",
          "src_module": "rv_decode",
          "src_port": "rs1"
        },
        {
          "dst_module": "rv_regfile",
          "dst_port": "raddr2",
          "src_module": "rv_decode",
          "src_port": "rs2"
        },
        {
          "dst_module": "rv_alu",
          "dst_port": "rs1_val",
          "src_module": "rv_regfile",
          "src_port": "rdata1"
        },
        {
          "dst_module": "rv_alu",
          "dst_port": "rs2_val",
          "src_module": "rv_regfile",
          "src_port": "rdata2"
        },
        {
          "dst_module": "rv_ctrl",
          "dst_port": "rs2_val",
          "src_module": "rv_regfile",
          "src_port": "rdata2"
        },
        {
          "dst_module": "rv_alu",
          "dst_port": "pc_val",
          "src_module": "rv_ctrl",
          "src_port": "pc"
        },
        {
          "dst_module": "rv_alu",
          "dst_port": "imm",
          "src_module": "rv_decode",
          "src_port": "imm"
        },
        {
          "dst_module": "rv_alu",
          "dst_port": "op",
          "src_module": "rv_decode",
          "src_port": "alu_op"
        },
        {
          "dst_module": "rv_alu",
          "dst_port": "a_sel",
          "src_module": "rv_decode",
          "src_port": "a_sel"
        },
        {
          "dst_module": "rv_alu",
          "dst_port": "b_sel",
          "src_module": "rv_decode",
          "src_port": "b_sel"
        },
        {
          "dst_module": "rv_ctrl",
          "dst_port": "kind",
          "src_module": "rv_decode",
          "src_port": "kind"
        },
        {
          "dst_module": "rv_ctrl",
          "dst_port": "funct3",
          "src_module": "rv_decode",
          "src_port": "funct3"
        },
        {
          "dst_module": "rv_ctrl",
          "dst_port": "rd",
          "src_module": "rv_decode",
          "src_port": "rd"
        },
        {
          "dst_module": "rv_ctrl",
          "dst_port": "y",
          "src_module": "rv_alu",
          "src_port": "y"
        },
        {
          "dst_module": "rv_ctrl",
          "dst_port": "eq",
          "src_module": "rv_alu",
          "src_port": "eq"
        },
        {
          "dst_module": "rv_ctrl",
          "dst_port": "lt",
          "src_module": "rv_alu",
          "src_port": "lt"
        },
        {
          "dst_module": "rv_ctrl",
          "dst_port": "ltu",
          "src_module": "rv_alu",
          "src_port": "ltu"
        },
        {
          "dst_module": "rv_regfile",
          "dst_port": "we",
          "src_module": "rv_ctrl",
          "src_port": "rf_we"
        },
        {
          "dst_module": "rv_regfile",
          "dst_port": "waddr",
          "src_module": "rv_ctrl",
          "src_port": "rf_waddr"
        },
        {
          "dst_module": "rv_regfile",
          "dst_port": "wdata",
          "src_module": "rv_ctrl",
          "src_port": "rf_wdata"
        },
        {
          "dst_module": "rv_dmem",
          "dst_port": "we",
          "src_module": "rv_ctrl",
          "src_port": "dmem_we"
        },
        {
          "dst_module": "rv_dmem",
          "dst_port": "addr",
          "src_module": "rv_ctrl",
          "src_port": "dmem_addr"
        },
        {
          "dst_module": "rv_dmem",
          "dst_port": "wdata",
          "src_module": "rv_ctrl",
          "src_port": "dmem_wdata"
        },
        {
          "dst_module": "rv_ctrl",
          "dst_port": "dmem_rdata",
          "src_module": "rv_dmem",
          "src_port": "rdata"
        }
      ],
      "external_ports": [
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "clk",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "rst",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "run",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "imem_we",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "imem_waddr",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 6
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "imem_wdata",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 32
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "pc",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 32
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "retire",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "rf_we",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "rf_waddr",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 5
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "rf_wdata",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 32
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "dmem_we",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "dmem_addr",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 5
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "dmem_wdata",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 32
        }
      ],
      "modules": [
        {
          "behavior": "Instruction memory of 64 words of 32 bits with one write port (the core's program loader) and one registered read port. State: mem[0..63] and the imem_rdata register; imem_rdata is a view of that register only. At each rising edge with rst low, using pre-edge values: imem_rdata = mem[imem_raddr] (read-first: a word written at this same edge is read with its old value), and if imem_we = 1 then mem[imem_waddr] = imem_wdata. A synchronous active-high rst at a rising edge clears all 64 words and imem_rdata to 0 and ignores imem_we at that edge; reset has no effect between edges. The contents are defined by that reset, never by initial values (initial blocks are rejected in RTL), so the program is loaded after reset. Python oracle: cycle-level model, one step per rising edge; keep the registers in state and return every output as it is after that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "imem_rdata": 0
              },
              "inputs": {
                "imem_raddr": 5,
                "imem_waddr": 5,
                "imem_wdata": 10485907,
                "imem_we": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "imem_rdata": 10485907
              },
              "inputs": {
                "imem_raddr": 5,
                "imem_waddr": 5,
                "imem_wdata": 10485907,
                "imem_we": 1,
                "rst": 0
              }
            },
            {
              "after_cycles": 3,
              "expected": {
                "imem_rdata": 0
              },
              "inputs": {
                "imem_raddr": 62,
                "imem_waddr": 63,
                "imem_wdata": 3735928559,
                "imem_we": 1,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "rv_imem",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "clk",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rst",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "imem_we",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "imem_waddr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 6
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "imem_wdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "imem_raddr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 6
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "imem_rdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 3,
            "kind": "sync",
            "signal": "rst"
          }
        },
        {
          "behavior": "Combinational RV32I decoder for the word instr. Fields always shown: rs1 = instr[19:15], rs2 = instr[24:20], rd = instr[11:7], funct3 = instr[14:12]. Immediates (sign extension replicates instr[31]): I = sext(instr[31:20]); S = sext({instr[31:25], instr[11:7]}); B = sext({instr[31], instr[7], instr[30:25], instr[11:8], 0}) (13 bits); U = {instr[31:12], 12 zero bits}; J = sext({instr[31], instr[19:12], instr[20], instr[30:21], 0}) (21 bits). By the full 7-bit opcode instr[6:0] (kind, a_sel, b_sel, alu_op, imm): 0110011 OP: kind 0, a_sel 0, b_sel 0, alu_op = {instr[30], funct3}, imm 0. 0010011 OP-IMM: kind 0, a_sel 0, b_sel 1, imm I, alu_op = {instr[30], funct3} when funct3 = 101 (SRLI/SRAI) else {0, funct3} (bit 30 is immediate data for the other OP-IMM instructions). 0110111 LUI: kind 0, a_sel 2, b_sel 1, alu_op 0, imm U. 0010111 AUIPC: kind 0, a_sel 1, b_sel 1, alu_op 0, imm U. 1101111 JAL: kind 4, a_sel 1, b_sel 1, alu_op 0, imm J. 1100111 JALR: kind 5, a_sel 0, b_sel 1, alu_op 0, imm I (funct3 ignored). 1100011 BRANCH: kind 3, a_sel 1, b_sel 1, alu_op 0, imm B. 0000011 LOAD: kind 1, a_sel 0, b_sel 1, alu_op 0, imm I (every load is a word load; funct3 ignored). 0100011 STORE: kind 2, a_sel 0, b_sel 1, alu_op 0, imm S (every store is a word store). Any other opcode: kind 6 (no operation), a_sel 0, b_sel 0, alu_op 0, imm 0. kind 7 is never produced. All outputs are functions of instr only. Python oracle: combinational and stateless; step returns the outputs for this step's inputs (latency 0, no clock and no reset port).",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "a_sel": 0,
                "alu_op": 13,
                "b_sel": 1,
                "funct3": 5,
                "imm": 1037,
                "kind": 0,
                "rd": 5,
                "rs1": 1,
                "rs2": 13
              },
              "inputs": {
                "instr": 1087427219
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "a_sel": 1,
                "alu_op": 0,
                "b_sel": 1,
                "funct3": 4,
                "imm": 4294967288,
                "kind": 3,
                "rd": 25,
                "rs1": 1,
                "rs2": 2
              },
              "inputs": {
                "instr": 4263562467
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "a_sel": 1,
                "alu_op": 0,
                "b_sel": 1,
                "funct3": 0,
                "imm": 4293918720,
                "kind": 4,
                "rd": 0,
                "rs1": 0,
                "rs2": 0
              },
              "inputs": {
                "instr": 2147483759
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 0,
          "latency_known": true,
          "name": "rv_decode",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "instr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rs1",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rs2",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rd",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "imm",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "alu_op",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 4
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "a_sel",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 2
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "b_sel",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "kind",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "funct3",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 3,
            "kind": "sync",
            "signal": "rst"
          }
        },
        {
          "behavior": "RV32I register file: 32 registers of 32 bits, x0 always reads 0, two registered read ports and one write port. State: x1..x31, rdata1 and rdata2 (outputs are views of those two registers only). At each rising edge with rst low, using pre-edge values: rdata1 = x[raddr1] and rdata2 = x[raddr2] (0 for index 0; read-first: a register written at this same edge is read with its old value), and if we = 1 and waddr != 0 then x[waddr] = wdata (writes to x0 are ignored). A synchronous active-high rst at a rising edge clears x1..x31, rdata1 and rdata2 to 0 and ignores we at that edge; reset has no effect between edges. Contents are defined by that reset, never by initial values. Python oracle: cycle-level model, one step per rising edge; keep the registers in state and return every output as it is after that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "rdata1": 0,
                "rdata2": 0
              },
              "inputs": {
                "raddr1": 7,
                "raddr2": 0,
                "rst": 0,
                "waddr": 7,
                "wdata": 305419896,
                "we": 1
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "rdata1": 305419896,
                "rdata2": 305419896
              },
              "inputs": {
                "raddr1": 7,
                "raddr2": 7,
                "rst": 0,
                "waddr": 7,
                "wdata": 305419896,
                "we": 1
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "rdata1": 0,
                "rdata2": 0
              },
              "inputs": {
                "raddr1": 0,
                "raddr2": 0,
                "rst": 0,
                "waddr": 0,
                "wdata": 4294967295,
                "we": 1
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "rv_regfile",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "clk",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rst",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "we",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "waddr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "raddr1",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "raddr2",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rdata1",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rdata2",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 3,
            "kind": "sync",
            "signal": "rst"
          }
        },
        {
          "behavior": "Combinational RV32I ALU with operand selection. a = rs1_val when a_sel = 0, pc_val when a_sel = 1, 0 when a_sel = 2 or 3; b = imm when b_sel = 1, else rs2_val. y by op[2:0], all modulo 2^32: 000 a + b when op[3] = 0, a - b when op[3] = 1; 001 a << b[4:0]; 010 1 if a < b as two's complement signed numbers else 0; 011 1 if a < b unsigned else 0; 100 a ^ b; 101 a >> b[4:0] logical when op[3] = 0, arithmetic (sign bit replicated) when op[3] = 1; 110 a | b; 111 a & b. op[3] is ignored for every op[2:0] other than 000 and 101. Comparison flags always compare the raw rs1_val and rs2_val (not a or b): eq = (rs1_val == rs2_val), lt = rs1_val < rs2_val signed, ltu = rs1_val < rs2_val unsigned. Python oracle: combinational and stateless; step returns the outputs for this step's inputs (latency 0, no clock and no reset port).",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "eq": 0,
                "lt": 1,
                "ltu": 0,
                "y": 4160749569
              },
              "inputs": {
                "a_sel": 0,
                "b_sel": 0,
                "imm": 0,
                "op": 13,
                "pc_val": 0,
                "rs1_val": 2147483664,
                "rs2_val": 4
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "eq": 0,
                "lt": 1,
                "ltu": 0,
                "y": 1
              },
              "inputs": {
                "a_sel": 0,
                "b_sel": 1,
                "imm": 1,
                "op": 2,
                "pc_val": 64,
                "rs1_val": 4294967295,
                "rs2_val": 1
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "eq": 1,
                "lt": 0,
                "ltu": 0,
                "y": 72
              },
              "inputs": {
                "a_sel": 1,
                "b_sel": 1,
                "imm": 4294967288,
                "op": 8,
                "pc_val": 64,
                "rs1_val": 5,
                "rs2_val": 5
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 0,
          "latency_known": true,
          "name": "rv_alu",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "a_sel",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 2
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "b_sel",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "op",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 4
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rs1_val",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rs2_val",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "pc_val",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "imm",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "y",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "eq",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "lt",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "ltu",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 3,
            "kind": "sync",
            "signal": "rst"
          }
        },
        {
          "behavior": "Data memory of 32 words of 32 bits with one shared address. State: mem[0..31] and the rdata register; rdata is a view of that register only. At each rising edge with rst low, using pre-edge values: rdata = mem[addr] (read-first: old contents when this edge also writes addr), and if we = 1 then mem[addr] = wdata. A synchronous active-high rst at a rising edge clears all 32 words and rdata to 0 and ignores we at that edge; reset has no effect between edges. Contents are defined by that reset, never by initial values. Python oracle: cycle-level model, one step per rising edge; keep the registers in state and return every output as it is after that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "rdata": 0
              },
              "inputs": {
                "addr": 9,
                "rst": 0,
                "wdata": 3405705229,
                "we": 1
              }
            },
            {
              "after_cycles": 2,
              "expected": {
                "rdata": 3405705229
              },
              "inputs": {
                "addr": 9,
                "rst": 0,
                "wdata": 3405705229,
                "we": 1
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "rv_dmem",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "clk",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rst",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "we",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "addr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "wdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 3,
            "kind": "sync",
            "signal": "rst"
          }
        },
        {
          "behavior": "Multi-cycle RV32I sequencer. Every output is a function of registered state only (no combinational path from any input). Registers, all reset to 0: state in {F=0, D=1, E=2, M=3, L=4, W=5}, pc[31:0], npc[31:0], res[31:0], sdata[31:0], rd_q[4:0], wb_q, st_q, ld_q. Outputs: pc = pc; imem_raddr = pc[7:2]; retire = (state == W); rf_we = (state == W) && wb_q; rf_waddr = rd_q; rf_wdata = res; dmem_we = (state == M) && st_q; dmem_addr = res[6:2]; dmem_wdata = sdata. Neighbours: kind, funct3 and rd come from the decoder of the fetched word, y/eq/lt/ltu from the ALU, rs2_val from register read port 2, dmem_rdata from data memory. At each rising edge with rst low, using pre-edge values: in F, state = D when run = 1, else stay in F (run is sampled only in F). In D, state = E. In E: wb_q = 1 when kind is 0, 1, 4 or 5, else 0; st_q = (kind == 2); ld_q = (kind == 1); rd_q = rd; sdata = rs2_val; res = pc + 4 when kind is 4 or 5, else y; with link = pc + 4 and branch condition taken by funct3 (000 eq, 001 !eq, 100 lt, 101 !lt, 110 ltu, 111 !ltu, 010 and 011 never taken): npc = y when kind == 4 or (kind == 3 and taken), npc = y with bit 0 cleared when kind == 5, else npc = link; state = M when kind is 1 or 2, else W. In M, state = L when ld_q, else W. In L, res = dmem_rdata and state = W. In W, pc = npc and state = F. Any other state value goes to F. kinds 6 and 7 are no-operations (no write, npc = link). So an instruction takes 4 cycles (F with run, D, E, W), a store 5 and a load 6; the register write and retire are visible during W, a store's dmem_we during M. Arithmetic is modulo 2^32. Synchronous active-high rst at a rising edge returns every register to its reset value; reset has no effect between edges. Python oracle: cycle-level model, one step per rising edge; keep the registers in state and return every output as it is after that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 3,
              "expected": {
                "dmem_addr": 13,
                "dmem_wdata": 85,
                "dmem_we": 0,
                "imem_raddr": 0,
                "pc": 0,
                "retire": 1,
                "rf_waddr": 3,
                "rf_wdata": 4660,
                "rf_we": 1
              },
              "inputs": {
                "dmem_rdata": 119,
                "eq": 0,
                "funct3": 0,
                "kind": 0,
                "lt": 0,
                "ltu": 0,
                "rd": 3,
                "rs2_val": 85,
                "rst": 0,
                "run": 1,
                "y": 4660
              }
            },
            {
              "after_cycles": 8,
              "expected": {
                "dmem_addr": 18,
                "dmem_wdata": 85,
                "dmem_we": 0,
                "imem_raddr": 18,
                "pc": 72,
                "retire": 0,
                "rf_waddr": 9,
                "rf_wdata": 72,
                "rf_we": 0
              },
              "inputs": {
                "dmem_rdata": 119,
                "eq": 0,
                "funct3": 1,
                "kind": 3,
                "lt": 1,
                "ltu": 0,
                "rd": 9,
                "rs2_val": 85,
                "rst": 0,
                "run": 1,
                "y": 72
              }
            },
            {
              "after_cycles": 5,
              "expected": {
                "dmem_addr": 8,
                "dmem_wdata": 43981,
                "dmem_we": 0,
                "imem_raddr": 0,
                "pc": 0,
                "retire": 1,
                "rf_waddr": 12,
                "rf_wdata": 2271560481,
                "rf_we": 1
              },
              "inputs": {
                "dmem_rdata": 2271560481,
                "eq": 1,
                "funct3": 2,
                "kind": 1,
                "lt": 0,
                "ltu": 0,
                "rd": 12,
                "rs2_val": 43981,
                "rst": 0,
                "run": 1,
                "y": 156
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "rv_ctrl",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "clk",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rst",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "run",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "kind",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "funct3",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 3
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rd",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "y",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "eq",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "lt",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "ltu",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rs2_val",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "dmem_rdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "pc",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "imem_raddr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 6
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "retire",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rf_we",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rf_waddr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rf_wdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "dmem_we",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "dmem_addr",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 5
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "dmem_wdata",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 32
            }
          ],
          "reset": {
            "active_high": true,
            "duration_cycles": 3,
            "kind": "sync",
            "signal": "rst"
          }
        }
      ],
      "top_name": "rv32i_core"
    },
    "sha256": "d929f337047f7bb940f69810db39b096a401f49b578661e9ee0a5b81ca45ee8c",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": null,
    "known": false,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\rv32i_core.v",
    "source_sha256": "a03d15f8693c8945a8f18c6dc9bc6e3ac1758034605717267206d623bb70dda8"
  },
  "edit_scope": {
    "children": [
      "rv_imem",
      "rv_decode",
      "rv_regfile",
      "rv_alu",
      "rv_dmem",
      "rv_ctrl"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top rv32i_core and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [],
    "top": "rv32i_core"
  },
  "execution_context": {
    "dependencies": [],
    "implementation": "out_of_context",
    "part": "xc7a35tcpg236-1",
    "period_ns": 10.0,
    "promotions": {
      "Designutils 20-1307": "ERROR",
      "Synth 8-327": "ERROR",
      "Synth 8-3352": "ERROR",
      "Synth 8-9873": "ERROR",
      "VRFC 10-3609": "ERROR"
    },
    "synthesis_template": "61e44d95134130552d86e050a4db65035952d348028dc942b327b8aced90b3d1",
    "tb": {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\inputs\\testbench_path.v",
      "sha256": "9504eb14e21f244002c7baa797758dd7834564fd2144019d91eade6a40f825dc"
    },
    "tools": {
      "vivado_bin": {
        "path": "C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\vivado.bat",
        "sha256": "4f9c05aea82a71c7086a9e5edf01ba16ea70255f69cf3420c58b805ec113e994"
      },
      "xelab_bin": {
        "path": "C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\xelab.bat",
        "sha256": "512a29ace988992d7fab14ca84f20f0b4515bb69ef1d5fef0a57c5f28b72c9b1"
      },
      "xsim_bin": {
        "path": "C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\xsim.bat",
        "sha256": "8819fbb54fdf9cbcaaf24c2bf72801b403d5c93e0990ba32408b56c666761d21"
      },
      "xvlog_bin": {
        "path": "C:\\AMDDesignTools\\2025.2\\Vivado\\bin\\xvlog.bat",
        "sha256": "512a29ace988992d7fab14ca84f20f0b4515bb69ef1d5fef0a57c5f28b72c9b1"
      }
    },
    "top": "rv32i_core"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\synth.tcl",
      "sha256": "853862f8f726d2a7010a7adbe730e637e4c7dad83aafd7159d9c848c1750498e",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/rv32i_core.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nputs $fp {set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/timing.xdc\"\r\nsynth_design -top rv32i_core -flatten_hierarchy rebuilt -mode out_of_context \r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-06/rv32i_core_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\timing.xdc",
      "sha256": "64b6a06a567f5142e3b71c9ec44440c46d1ff02057a9207ab3820113a8e3e958",
      "text": "create_clock -period 10.000 -name clk [get_ports clk]\r\nset_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]\r\n",
      "truncated": false
    }
  ],
  "implementation": {
    "meaning": "Out-of-context implementation (chip_top_flow_for_soc_block): the top is a block inside a larger design, synthesized with synth_design -mode out_of_context and placed and routed without I/O buffers or package pins. clk is constrained at the target period and modeled as driven by a global clock buffer (HD.CLK_SRC). Data ports have no input or output delay and no pad delay, so they are unconstrained I/O; the routed WNS and WHS, and timing acceptance, cover the internal clocked paths only, and combinational logic between a port and its first or last register is not timed. Utilization excludes I/O buffers.",
    "mode": "out_of_context"
  },
  "part": "xc7a35tcpg236-1",
  "report_manifest": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\power.rpt",
      "sha256": "2321621efc6a0d27767b9ef8ccf086610361498637c98911532706d1a9a46121"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\timing.rpt",
      "sha256": "28433bfc887f0c80554dd4ec81e7f829395439e5f84e41850e2c5617bffcc962"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "beaecfde391ae55cd6dda213f865e8531db9580b8b95d0b401ead560a63c13f5"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\timing_routed.rpt",
      "sha256": "7667c2c33ebb12319ab8c8183530bdb284df235a2d80684d481259ac12b4156e"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\utilization.rpt",
      "sha256": "9919e1437d09e9fd2a2e494081d1f46b2934a985c60cff499aac8f01b789df12"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\utilization_routed.rpt",
      "sha256": "336871aa42d58f1befb7641a2f81d528108b687974f405e95ab99fef8db6773c"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\iter_000\\rv32i_core.v",
      "sha256": "a03d15f8693c8945a8f18c6dc9bc6e3ac1758034605717267206d623bb70dda8"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-06\\rv32i_core_build\\inputs\\testbench_path.v",
    "sha256": "9504eb14e21f244002c7baa797758dd7834564fd2144019d91eade6a40f825dc"
  },
  "testbench_top": "rv32i_core_tb",
  "top_module": "rv32i_core"
}
```
