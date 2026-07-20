---
name: testbench-craft
description: "Use when writing, generating, or debugging testbenches: self-checking discipline, scoreboards, stimulus corners, latency handling, and the reset/X window."
---
# Testbench Craft

## Self-checking discipline
- Machine-parsable verdict lines only: `TEST PASSED` / `TEST FAILED: N errors`.
- Every mismatch prints one line: `FAIL index=%0d signal=... expected=%0d got=%0d`.
- Use `!==` (4-state compare) so X propagation is caught, not masked.

## The reset/X window
Hardware wakes up as X. Apply reset per the contract (kind, polarity, duration), then wait a 2-cycle settle margin, and ONLY THEN open the comparison window. Comparing at t=0 is a false failure generator.

## Latency handling — two modes
- **fixed_latency**: delay expected outputs by N cycles (software shift register in the tb) before compare. N comes from the contract.
- **scoreboard (valid/ready)**: push expected output when an input beat is accepted (`valid&&ready`); pop-and-compare when an output beat fires. Latency becomes irrelevant; order+values are the truth. Exercise backpressure by periodically deasserting ready.

## Stimulus corners that catch real bugs
- all-zeros, all-ones, MSB-only (sign bugs)
- wrap boundaries (max value + 1)
- back-to-back operations with no idle cycle
- enable deasserted mid-operation
- reset asserted mid-operation (if the contract requires recovery)

## Oracle qualification (why your tb must fail sometimes)
A testbench is only trusted after it FAILS a sabotaged design (mutated operator or off-by-one). A tb that passes broken code is itself broken.
