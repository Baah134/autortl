# Tier0 campaign23: no verdict (the Codex CLI binary moved)

The rerun of the third gate on the final 249-file identity (freeze
`022ab35a…`). Its full test receipt passed (1,601 tests), but every model call
then failed with `CODEX_UNAVAILABLE: worker could not launch`. The Codex
desktop app had updated itself at 20:24 EDT and replaced its versioned binary
folder, so `AUTORTL_CODEX_BIN` pointed at a file that no longer existed.

Both entries ended `model_blocked` with `failure_kind: infra`. The new rule
did its job: the campaign got no verdict, nothing was written to the
curriculum history, and the bench exited 3. The tier0 streak on this identity
stays at 2.

Fix: `tools/tier0_gate.py` now runs `run.py doctor` before freezing the source
or starting the test receipt, and refuses to start when a required tool or the
model CLI is missing, so this fails in seconds instead of after the receipt.
