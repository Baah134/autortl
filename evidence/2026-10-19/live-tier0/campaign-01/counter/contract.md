# CONTRACT

## Resource targets
- [ ] In a clean Vivado Design Suite **2023.2** project targeting `xc7a35tcpg236-1`, synthesize top module `counter` with exactly `synth_design -top counter -part xc7a35tcpg236-1 -flatten_hierarchy none`. Use no synthesis settings or passes beyond that command and Vivado’s defaults. In the post-synthesis `report_utilization`, check the hierarchical total for `counter`, including all instantiated child modules. **Slice LUTs** must be no more than **45**.
- [ ] In the same report and hierarchy scope, **Slice Registers** must be no more than **37**, and **DSPs** and **Block RAM Tile** must each be **0**.

## Timing targets
- [ ] Apply only these timing constraints: `create_clock -name clk -period 10.000 [get_ports clk]`; minimum and maximum input delays of `0.000 ns` on every non-clock input port relative to `clk`; minimum and maximum output delays of `0.000 ns` on every output port relative to `clk`; and clock uncertainty of `0.000 ns`. No other timing constraints are permitted.
- [ ] In the clean Vivado Design Suite **2023.2** project, run the implementation commands in this order, with no additional settings, passes, or changed directives: `opt_design`, `place_design`, `phys_opt_design`, and `route_design`.
- [ ] Set the operating condition with `set_operating_conditions -process slow -voltage 0.950 -temperature 85`. After `route_design`, run `report_timing_summary -delay_type max` with that operating condition active. The report must identify **slow process**, **0.950 V**, and **85 °C**; the reported **WNS** must be at least **5.000 ns**.

## Correctness
- [ ] The complete `counter` module port list must be: inputs `clk`, `rst`, `load`, and `enable`, each 1 bit; input `load_val`, 32 bits; output `count`, 32 bits; and outputs `overflow`, `at_zero`, `below_low`, `below_mid`, and `below_high`, each 1 bit. Use `WIDTH = 32`. Declare `count` and `load_val` as unsigned 32-bit vectors. `rst` is active-high and synchronous: on a rising edge of `clk` when `rst` is high, `count` and `overflow` clear to 0, and all four flags set to 1.
- [ ] On a rising edge of `clk` when `rst` is low, `load` loads `load_val` into `count` and clears `overflow`, taking priority over `enable`. With `enable` high and `load` low, `count` increments modulo `2^32`; `overflow` is set to 1 only when the pre-edge `count` is `32'hFFFF_FFFF`, and is cleared on every other enabled increment. With both `load` and `enable` low, `count` and `overflow` hold their values.
- [ ] On every rising edge of `clk`, each flag captures its comparison against the pre-edge `count`, except that reset sets all four flags to 1: `at_zero` captures `count == 32'd0`; `below_low` captures `count < 32'd10`; `below_mid` captures `count < 32'd20`; and `below_high` captures `count < 32'd30`.
- [ ] Run testbench `tb_counter` with Vivado Simulator (**XSim 2023.2**) using `xvlog -sv tb_counter.sv counter.sv`, `xelab tb_counter -s tb_counter_sim`, and `xsim tb_counter_sim -runall`. The testbench must use assertions or expected-value checks, sample outputs after each rising edge’s nonblocking assignments have taken effect, print `PASS` only if every check succeeds, and terminate with a nonzero simulator exit code on any failure.
- [ ] The testbench must apply the following stimulus in order, holding each row’s inputs through the indicated rising edge. `load_val` is `32'd0` when its value is shown as `—`. For every row, check `count`, `overflow`, and all four flags against the expected post-edge values shown.

  | Rising edge | `rst` | `load` | `enable` | `load_val` | Expected `count` | Expected `overflow` | Expected `{at_zero, below_low, below_mid, below_high}` |
  |---:|---:|---:|---:|---:|---:|---:|---:|
  | 1 | 1 | 0 | 0 | — | `32'd0` | 0 | `4'b1111` |
  | 2 | 0 | 1 | 1 | `32'd10` | `32'd10` | 0 | `4'b1111` |
  | 3 | 0 | 0 | 0 | — | `32'd10` | 0 | `4'b0111` |
  | 4 | 0 | 0 | 1 | — | `32'd11` | 0 | `4'b0111` |
  | 5 | 0 | 1 | 1 | `32'hFFFF_FFFF` | `32'hFFFF_FFFF` | 0 | `4'b0111` |
  | 6 | 0 | 0 | 1 | — | `32'd0` | 1 | `4'b0000` |
  | 7 | 0 | 0 | 0 | — | `32'd0` | 1 | `4'b1111` |
  | 8 | 1 | 0 | 0 | — | `32'd0` | 0 | `4'b1111` |
  | 9 | 0 | 1 | 0 | `32'd20` | `32'd20` | 0 | `4'b1111` |
  | 10 | 0 | 0 | 0 | — | `32'd20` | 0 | `4'b0001` |
  | 11 | 0 | 1 | 0 | `32'd30` | `32'd30` | 0 | `4'b0001` |
  | 12 | 0 | 0 | 0 | — | `32'd30` | 0 | `4'b0000` |

## Code quality
- [ ] The RTL contains exactly **one nonblocking assignment to `count` in the entire source file**. Count every source-level `<=` assignment whose left-hand side is `count`; the total must be one, regardless of control-flow branches.
- [ ] The only sequential state registers are `count`, `overflow`, `at_zero`, `below_low`, `below_mid`, and `below_high`. No additional sequential variables or inferred storage elements are permitted, and the RTL must infer no latches. Combinational temporaries are permitted only if they infer no storage. `count` is exactly **32 bits** wide.

## Definition of done

Complete when every checklist item passes, the specified Vivado reports meet the resource and timing targets for `xc7a35tcpg236-1`, and the specified `tb_counter` simulation passes.