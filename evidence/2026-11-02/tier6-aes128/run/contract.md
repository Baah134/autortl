# Fixed optimization contract

This contract is rendered by the harness from immutable run evidence. Planner, generator and evaluator cannot amend its requirements.

## Behavioral obligations

The complete resolved typed build specification below is the behavioral authority. Preserve all defined behavior, supported parameter semantics, reset priority, observable cycles, latency, throughput, flags and handshakes. Preserve top ports and parameter defaults. Explicitly unspecified cases remain unspecified: do not impose blanket equality to incidental frozen implementation values in those cases, including invalid output payload when the spec leaves it unspecified. This does not relax specified valid payloads, transfers or cycle behavior. Source hashes identify the measured implementation, not additional semantic obligations. No new pipeline stages, extra cycles, interfaces or invented thresholds.

## Edit boundary

The editable source is one unit holding every generated child module (aes_ctrl, aes_round, aes_key_step) and the top aes128_core, children first and top last; no frozen companion is compiled beside it. Only the top aes128_core carries the interface contract: its name, ports, parameters and defaults, reset, clocking, latency annotation rule and every observable cycle at its ports are fixed. Child module names, ports and boundaries are internal and may change while the top's contract holds. Every candidate must define aes128_core. Every candidate is verified by the trusted integration testbench below and every other gate. The per-child generated oracles and testbenches verified the baseline children only; they are not evidence for changed children and must not be cited as such. Typed child contracts in the build spec describe the baseline decomposition; their composed behavior at the top's ports remains mandatory. Their latency fields and annotations bind nothing on their own: a child module needs no // @latency annotation, and a missing or changed child annotation is never a failed criterion (evaluator_requires_child_latency_annotation).

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
    "bram_used": 1.5,
    "dsp_total": 90,
    "dsp_used": 0,
    "dynamic_power_w": 2.589,
    "ff_pct": 0.6298076923076923,
    "ff_total": 41600,
    "ff_used": 262,
    "lut_pct": 43.78846153846154,
    "lut_total": 20800,
    "lut_used": 9108,
    "reg2reg_wns_ns": -9.76,
    "sim_error": "",
    "sim_passed": true,
    "synth_error": "",
    "timing_met": false,
    "total_power_w": 2.664,
    "whs_ns": 0.204,
    "wns_ns": -9.76
  },
  "build_spec": {
    "authority": "Complete resolved typed build contract. Defined behavior is mandatory; explicitly unspecified cases remain unspecified. Frozen implementation identities do not turn incidental values in unspecified cases into requirements.",
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\design_spec.json",
    "resolved_spec": {
      "connections": [
        {
          "dst_module": "aes_round",
          "dst_port": "state_in",
          "src_module": "aes_ctrl",
          "src_port": "ct"
        },
        {
          "dst_module": "aes_round",
          "dst_port": "round_key",
          "src_module": "aes_ctrl",
          "src_port": "rk"
        },
        {
          "dst_module": "aes_round",
          "dst_port": "final_round",
          "src_module": "aes_ctrl",
          "src_port": "last"
        },
        {
          "dst_module": "aes_ctrl",
          "dst_port": "round_out",
          "src_module": "aes_round",
          "src_port": "state_out"
        },
        {
          "dst_module": "aes_key_step",
          "dst_port": "key_in",
          "src_module": "aes_ctrl",
          "src_port": "rk"
        },
        {
          "dst_module": "aes_key_step",
          "dst_port": "rcon",
          "src_module": "aes_ctrl",
          "src_port": "rcon"
        },
        {
          "dst_module": "aes_ctrl",
          "dst_port": "key_next",
          "src_module": "aes_key_step",
          "src_port": "key_out"
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
          "name": "in_valid",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "in_ready",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "key",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 128
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "pt",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 128
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "out_valid",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "input",
          "name": "out_ready",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 1
        },
        {
          "clock_domain": "clk",
          "direction": "output",
          "name": "ct",
          "packed_dimensions": null,
          "protocol": "none",
          "signed": false,
          "width": 128
        }
      ],
      "modules": [
        {
          "behavior": "Iterative AES-128 encryption sequencer (FIPS-197) with a valid/ready-style input and output; the handshake ports are plain protocol none signals. Blocks are 128-bit big-endian byte strings: byte 0 is bits [127:120]. Registers, all reset to 0: busy, out_valid, rnd[3:0], ct[127:0] (the state), rk[127:0] (the round key). Outputs, all views of registered state: in_ready = !busy && !out_valid; out_valid; ct; rk; last = (rnd == 10); rcon = 01, 02, 04, 08, 10, 20, 40, 80, 1b, 36 (hex) for rnd = 0..9 and 00 for rnd = 10..15. Neighbours: round_out = AES round of (ct, round key rk, final round = last); key_next = key-schedule step of (rk, rcon). At each rising edge with rst low, using pre-edge values: if busy: rk = key_next; then if rnd == 0 (key preparation) rnd = 1; else ct = round_out and, when rnd == 10, busy = 0, out_valid = 1, rnd = 0, otherwise rnd = rnd + 1. Else if out_valid: out_valid = 0 when out_ready = 1 (ct holds). Else (idle) if in_valid = 1: accept: ct = pt ^ key (initial AddRoundKey), rk = key, rnd = 0, busy = 1. key, pt and in_valid are ignored except at the accepting edge, out_ready only while out_valid. An accepted block takes 11 busy edges (key preparation, rounds 1..10) and out_valid with ct = ciphertext appears after the 11th; the next block can be accepted at the edge after the output transfer at the earliest. Synchronous active-high rst at a rising edge returns every register to its reset value; reset has no effect between edges. Python oracle: cycle-level model, one step per rising edge; keep the registers in state and return every output as it is after that edge. The driver applies the fixed latency of 1; do not add a delay queue. init() is the reset state and a supplied rst must be handled.",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "ct": 83729609699884896815286331701780720,
                "in_ready": 0,
                "last": 0,
                "out_valid": 0,
                "rcon": 1,
                "rk": 5233100606242806050955395731361295
              },
              "inputs": {
                "in_valid": 1,
                "key": 5233100606242806050955395731361295,
                "key_next": 340193404210632335760508365704335069440,
                "out_ready": 0,
                "pt": 88962710306127702866241727433142015,
                "round_out": 1512366075204170928972419503379277431,
                "rst": 0
              }
            },
            {
              "after_cycles": 11,
              "expected": {
                "ct": 1512366075204170928972419503379277431,
                "in_ready": 0,
                "last": 1,
                "out_valid": 0,
                "rcon": 0,
                "rk": 340193404210632335760508365704335069440
              },
              "inputs": {
                "in_valid": 1,
                "key": 5233100606242806050955395731361295,
                "key_next": 340193404210632335760508365704335069440,
                "out_ready": 0,
                "pt": 88962710306127702866241727433142015,
                "round_out": 1512366075204170928972419503379277431,
                "rst": 0
              }
            },
            {
              "after_cycles": 14,
              "expected": {
                "ct": 33552049213138075477934976549088937992,
                "in_ready": 0,
                "last": 0,
                "out_valid": 0,
                "rcon": 1,
                "rk": 57811460909138771071931939740208549692
              },
              "inputs": {
                "in_valid": 1,
                "key": 57811460909138771071931939740208549692,
                "key_next": 276588332753250198369059907516451982502,
                "out_ready": 1,
                "pt": 66814286504060421741230023322616923956,
                "round_out": 75960790320075369159181001580855561010,
                "rst": 0
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 1,
          "latency_known": true,
          "name": "aes_ctrl",
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
              "name": "in_valid",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "in_ready",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "key",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "pt",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "out_valid",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "out_ready",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "ct",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rk",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "rcon",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "last",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "round_out",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "key_next",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
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
          "behavior": "Combinational AES encryption round (FIPS-197). Bytes are big-endian: byte n (0..15) of a 128-bit value is bits [127-8n:120-8n], and byte n sits at row n % 4, column n // 4 of the state. state_out = AddRoundKey(MixColumns(ShiftRows(SubBytes(state_in))), round_key) when final_round = 0, and AddRoundKey(ShiftRows(SubBytes(state_in)), round_key) when final_round = 1. SubBytes applies the AES S-box to every byte (the multiplicative inverse in GF(2^8) modulo x^8 + x^4 + x^3 + x + 1, 0 mapping to 0, followed by the affine map b ^ rotl(b,1) ^ rotl(b,2) ^ rotl(b,3) ^ rotl(b,4) ^ 0x63; S(00) = 63, S(01) = 7c, S(53) = ed). ShiftRows rotates row r left by r: new byte at (r, c) = old byte at (r, (c + r) % 4). MixColumns maps each column (a0, a1, a2, a3), a0 at row 0, to (2a0^3a1^a2^a3, a0^2a1^3a2^a3, a0^a1^2a2^3a3, 3a0^a1^a2^2a3) in GF(2^8). AddRoundKey is a 128-bit XOR. Python oracle: combinational and stateless; step returns the outputs for this step's inputs (latency 0, no clock and no reset port).",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "state_out": 218805984690271539793496889057209897033
              },
              "inputs": {
                "final_round": 0,
                "round_key": 213979707136699034080426665618942227973,
                "state_in": 33552049213138075477934976549088937992
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "state_out": 75960790320075369159181001580855561010
              },
              "inputs": {
                "final_round": 1,
                "round_key": 276588332753250198369059907516451982502,
                "state_in": 312705796755970461592149921386262119122
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 0,
          "latency_known": true,
          "name": "aes_round",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "state_in",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "round_key",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "final_round",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 1
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "state_out",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
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
          "behavior": "Combinational AES-128 key-schedule step (FIPS-197 KeyExpansion, one round key at a time). key_in = {w0, w1, w2, w3} with w0 = key_in[127:96]; temp = SubWord(RotWord(w3)) ^ {rcon, 24 zero bits}, where RotWord({a0, a1, a2, a3}) = {a1, a2, a3, a0} (a0 the most significant byte) and SubWord applies the AES S-box (as in aes_round) to each byte; w4 = w0 ^ temp, w5 = w1 ^ w4, w6 = w2 ^ w5, w7 = w3 ^ w6; key_out = {w4, w5, w6, w7}. rcon is used as given (any 8-bit value). Python oracle: combinational and stateless; step returns the outputs for this step's inputs (latency 0, no clock and no reset port).",
          "clock_domains": [
            "clk"
          ],
          "compare_mode": "fixed_latency",
          "examples": [
            {
              "after_cycles": 1,
              "expected": {
                "key_out": 213979707136699034080426665618942227973
              },
              "inputs": {
                "key_in": 57811460909138771071931939740208549692,
                "rcon": 1
              }
            },
            {
              "after_cycles": 1,
              "expected": {
                "key_out": 276588332753250198369059907516451982502
              },
              "inputs": {
                "key_in": 229247186667434634296614468440630755438,
                "rcon": 54
              }
            }
          ],
          "golden_model": "",
          "interface_signature": null,
          "latency": 0,
          "latency_known": true,
          "name": "aes_key_step",
          "parameters": {},
          "ports": [
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "key_in",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
            },
            {
              "clock_domain": "clk",
              "direction": "input",
              "name": "rcon",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 8
            },
            {
              "clock_domain": "clk",
              "direction": "output",
              "name": "key_out",
              "packed_dimensions": null,
              "protocol": "none",
              "signed": false,
              "width": 128
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
      "top_name": "aes128_core"
    },
    "sha256": "281f650d2a81d2b478ca91d376a5abf0997c513719920b80f1bcd9231c827e8e",
    "truncated": false
  },
  "clock_period_ns": 10.0,
  "declared_latency": {
    "cycles": null,
    "known": false,
    "meaning": "A source annotation declares numeric latency only when present. This known/cycles pair is authoritative for the current top module's annotation requirement. Only known=true requires a matching numeric top annotation. Child typed-module latency does not invent a top annotation for arbitrary aggregate wrappers. When known=false, absence of a top annotation is not a failed or unverifiable criterion. Unannotated numeric latency is UNKNOWN, not zero. Preserve the source's exact observable cycles and registered behavior. Annotation presence or absence alone is not independent proof of behavioral correctness; use the fixed source contract, all defined typed latency/minimum transfer age and deterministic verification, without inventing a numeric requirement.",
    "source_path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\aes128_core.v",
    "source_sha256": "c353920b2d1ee5a106050ea6567b8368617d1b0a8ac2cf4d78f70323be1ba073"
  },
  "edit_scope": {
    "children": [
      "aes_ctrl",
      "aes_round",
      "aes_key_step"
    ],
    "mode": "whole_design",
    "reason": "The supplied testbench instantiates the top aes128_core and is the trusted integration authority, so every generated child module and the mechanical top form one editable unit verified through the top. Per-child generated oracles and testbenches verified the baseline children only and are not evidence for changed children.",
    "testbench_modules": [],
    "top": "aes128_core"
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\inputs\\testbench_path.v",
      "sha256": "663853132a1f7736225fd253a46215ae0ddfa06372ff1a83a79dcc2051feb34e"
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
    "top": "aes128_core"
  },
  "flow_and_constraints": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\synth.tcl",
      "sha256": "2977c25d80e24af7eb0eedf438558c7531b7e540a779c5f2480802d6c5ccb435",
      "text": "set_msg_config -id {VRFC 10-3609} -new_severity ERROR\r\nset_msg_config -id {Synth 8-9873} -new_severity ERROR\r\nset_msg_config -id {Designutils 20-1307} -new_severity ERROR\r\nset_msg_config -id {Synth 8-327} -new_severity ERROR\r\nset_msg_config -id {Synth 8-3352} -new_severity ERROR\r\nset_part xc7a35tcpg236-1\r\nread_verilog \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/aes128_core.v\"\r\nset fp [open \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing.xdc\" w]\r\nputs $fp {create_clock -period 10.000 -name clk [get_ports clk]}\r\nputs $fp {set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]}\r\nclose $fp\r\nread_xdc \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing.xdc\"\r\nsynth_design -top aes128_core -flatten_hierarchy rebuilt -mode out_of_context \r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/utilization.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing.rpt\"\r\nopt_design\r\nplace_design\r\n\r\nroute_design\r\nreport_utilization -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/utilization_routed.rpt\"\r\nreport_timing_summary -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing_routed.rpt\"\r\ncatch { if {[llength [all_registers]] > 0} { report_timing -from [all_registers] -to [all_registers] -max_paths 1 -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/timing_reg2reg.rpt\" } }\r\nreport_design_analysis -logic_level_distribution -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/design_analysis.rpt\"\r\nreport_power -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/power.rpt\"\r\ncatch { report_methodology -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/methodology.rpt\" }\r\ncatch { report_qor_suggestions -file \"C:/Users/prince.baah/Downloads/autortl-work/logs/explore-tier6-07/aes128_core_build/iter_000/qor_suggestions.rpt\" }\r\nputs \"SYNTH_COMPLETE\"\r\n",
      "truncated": false
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\timing.xdc",
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
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\power.rpt",
      "sha256": "ad1d72ccf46c94ee0229b81fa87a4d6e9fc1b71ca602463500b9ec37480a7b05"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\timing.rpt",
      "sha256": "1695848307272d5fed1d95f2f1de1b87b7ee7db7fdf6661e226358f55929faa6"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\timing_reg2reg.rpt",
      "sha256": "278f2f28b54ac5fc6837131c9c252d103cf55db66d3fc1b628022a281cc9ab7b"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\timing_routed.rpt",
      "sha256": "36183a99179ac7bd71e2fa764df850c9e1a2a08de343102e5c7b552d839fded3"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\utilization.rpt",
      "sha256": "e6b0428ed5cf59534569409d3ac1392f84b381c1ac843df0fe0f824f7d081b0c"
    },
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\utilization_routed.rpt",
      "sha256": "6c69f401dc9879ddc55daa545cf363eeec3ee32918968fe01cc7a1a087701f53"
    }
  ],
  "sources": [
    {
      "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\iter_000\\aes128_core.v",
      "sha256": "c353920b2d1ee5a106050ea6567b8368617d1b0a8ac2cf4d78f70323be1ba073"
    }
  ],
  "testbench": {
    "path": "C:\\Users\\prince.baah\\Downloads\\autortl-work\\logs\\explore-tier6-07\\aes128_core_build\\inputs\\testbench_path.v",
    "sha256": "663853132a1f7736225fd253a46215ae0ddfa06372ff1a83a79dcc2051feb34e"
  },
  "testbench_top": "aes128_core_tb",
  "top_module": "aes128_core"
}
```
