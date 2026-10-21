# Parameterized synchronous FIFO admission

**836 full regression tests passed in270.94seconds.** Fixture focus26tests and
runner focus29tests passed. Real serial simulation produced14/14expected
verdicts: the supervised control passed, and all13planned faults produced raw
behavioral assertion failures. Compilation errors, timeouts and infrastructure
failures do not count as killed faults. This is a selected fault set, not a
universal mutation score or formal correctness proof.

Independent default wrapper8x3 and child corners1x1,8x2,8x4,13x5,16x8 each passed.
Their checked cycles were721,701,711,731,741,771 respectively. Each checker covers
exact capacity/readiness, simultaneous full transfers, stalls/order/all payload
bits, non-power-of-two wrap where relevant, synchronous occupied reset and final
accepted=retired+discarded accounting. Only the enclosing TB emits a verdict
after all finish. No DUT internals serve as reference state.

Faults cover hardcoded depth or memory width, power-of-two-only wrap, early/late
full, blocked or lost simultaneous transfers, output truncation, unstable stalls,
incorrect order, asynchronous reset and combinational bypass. Full source/TB
hashes, exact mutation targets, all raw logs and actual process receipts remain.
The qualification reference is never a generated winner or model seed.

```powershell
python scripts/check_build_tbs.py --suite fifo --bin-dir $vivadoBin --output runs/fifo-admission
```

See curriculum/tier2/sync_fifo_build for the fixed contract and six-case matrix.
The existing harness runtime remains8098466; this milestone adds the experiment
and extends its existing serial runner. No generated FIFO PPA result is claimed
by admission. Source bytes are bound by manifests; a future model build records
its own source commit and input identities. Archives omit compiled simulator
and journal artifact trees and are not directly resumable folders.
