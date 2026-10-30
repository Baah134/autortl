# Tier0 campaign26: no verdict (Codex usage limit)

The third gate on the hardened 272-file identity. `run.py doctor` and the
full test receipt (1,654 tests) passed, then every model call failed:
"You've hit your usage limit ... try again at 1:45 AM". Both entries ended
`model_blocked` with `failure_kind: infra` (CODEX_QUOTA), so the campaign got
no verdict and nothing entered the curriculum history; the tier0 streak on
this identity stays at 2. The third gate is rerun as contract-campaign-27
after the limit resets.
