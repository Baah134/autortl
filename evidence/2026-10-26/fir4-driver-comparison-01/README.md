# Generated scoreboard driver comparison01

Actual measurement status: **completed**. The frozen FIR reference
passed;
**22/27** named faults detected, **5** missed,
**0** ungraded or unexecuted. All27 remain in the denominator.
See comparison/result.json and individual raw logs/process receipts.

The five nominal traffic controls are separate: **5/5**
passed their required coverage. The deliberately bad producer-driver probe
was detected;
it is not an RTL mutant and is not added to the27-fault score.

The old generated FIR oracle, reference and all fault sources were frozen.
The110 signed-only payload/expected arrays stayed byte-identical; only generated
driver scheduling changed. Source snapshots retain230 staged files, while the
canonical228-file source and original build artifacts/budget/router statistics
stayed unchanged. No models or synthesis were invoked. Actual measured wall
time was 415.375 seconds.

The driver exercises legal bubbles with changing invalid payloads and synchronous
off-edge reset pulses, while preserving blocked offers. It does not add an
occupied rising-edge reset policy or require ports to remain invariant while
reset is asserted. Async-reset contracts receive no unmodelled pulses.
Selected fault sensitivity is not formal equivalence or a model-strength claim.
No resource, power or timing improvement follows from this verification audit.

The original4-failed/6-passed pre-patch log and117-test focused result are
preserved. The command addendum transparently supplies the omitted original
basetemp argument; it does not rewrite the original receipt. Binary simulator
builds are omitted; archive-manifest.json defines the retained raw artifacts.
