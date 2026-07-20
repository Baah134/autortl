Build a button debouncer named `debouncer`.
Inputs: clk, rst (sync, active-high, 5 cycles), noisy (1 bit).
Output: clean (1 bit).
Behavior: `clean` takes the value of `noisy` only after `noisy` has held the
same value for 8 consecutive clock cycles. Until then `clean` holds its old
value. After reset, clean = 0. Latency: n/a (level-based, use fixed_latency 0
with examples that respect the 8-cycle hold).
