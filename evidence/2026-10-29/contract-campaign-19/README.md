# Tier0 campaign19: aborted during its test receipt (no verdict)

Started on the merged harness (895431f, 243-file freeze) with
`--model gpt-6-luna --jobs 2`. While its full test receipt ran, the
supervisor launched three Claude Code subagents with isolated git worktrees,
which Claude Code places under `.claude/worktrees/`. The gate's source
identity hashed everything under `.claude`, so those new checkouts would
have made the after-tests identity check fail and the bench would never have
launched. The supervisor stopped the gate before the receipt finished.
Nothing reached the bench or the curriculum history.

Fix: `tools/tier0_gate.py` now skips `.claude/worktrees/`, and
`.gitignore` ignores it. The live identity is back to the same 243 files.

Kept here: the freeze and the console log.
