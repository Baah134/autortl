# Session handoff

Updated: 2026-10-15 (America/New_York)

## Objective and decisions

Build a reliable autonomous RTL improvement loop, starting with small
designs and increasing complexity only after demonstrated correctness.
Keep evidence suitable for the owner's CV. Use command-line Vivado now;
MCP is deferred. No background schedule is configured.

## Source state

- Repository: Baah134/autortl; base commit
  `ee255942452f4d021d289512830f63d1cdb3c035`.
- Active development branch: `codex/cli-bringup`.
- Continuity documentation and repairs are checkpointed on this local branch;
  no remote publication yet. Consult `git log -1` for the checkpoint commit.
- MCP draft preserved in a local Git stash named
  `Paused MCP integration draft; user selected CLI`, originating on
  `codex/vivado-mcp-setup`. It is not a portable remote backup.
- Local repairs now cover simulation verdicts, mutation qualification,
  candidate verification gates, counter stimulus, and XDC generation.
  See PROGRESS for evidence. These changes are not merged or published.

## Verified evidence

- Initial review: 91 existing tests passed with Python 3.12 in 4.30 seconds.
  This is historical baseline evidence, not a new run this session.
- Controlled review probes exposed false-success, resume, interface, build,
  qualification, and artifact/metrics consistency defects.
- Vivado 2025.2 batch Tcl smoke passed this session, exit code 0:
  version 2025.2; expression `6 * 7` returned 42; success marker emitted.
- Windows sandbox launch failed; approved execution outside the sandbox
  succeeded. Future Vivado jobs may also require that execution approval.
- Follow-up: 128 unit tests passed (37 added to the reviewed 91-test baseline).
- Real counter simulation passed after fixing an extra enabled clock edge.
  Real mutation qualification passed: a flipped comparison was detected.
- Initial synthesis reproduced Common 17-53 (premature get_ports evaluation).
  XDC generation fixed; counter completed placement/routing at 10 ns on
  xc7a35tcpg236-1: 54 LUTs, 37 FFs, WNS 5.491 ns, WHS 0.276 ns.
- Raw timing comparison also exposed and fixed hold-slack column parsing.
- Reusable counter CLI check passed end to end, exit code 0; evidence in
  `work/counter_cli_complete`. Raw JSON has a stale simulation-error field
  explained in PROGRESS; explicit simulation verdict/log passed. Metadata
  cleanup is unit tested, not separately rerun through all Vivado stages.
- Autonomous optimization and quantitative improvement remain unestablished.
- GitHub connector reported push permission; no remote write exercised.

## Local evidence and environment

Workspace-relative locations (workspace contains `work/autortl`):

- `outputs/AutoRTL-review.md`: detailed repository review.
- `outputs/AutoRTL-review-evidence.json`: controlled probe evidence.
- `outputs/AutoRTL-progress-log.md`: original progress record.
- `work/vivado-cli-smoke/check.tcl`: successful smoke source.
- `work/review_deps`: baseline Python test dependencies.
- Vivado launcher: `C:/AMDDesignTools/2025.2/Vivado/bin/vivado.bat`.
- Python: bundled Codex Python 3.12; default Python 3.14 was unsuitable.

These workspace artifacts are local, not yet committed alongside the repo.

## Next action

Use `scripts/check_counter_cli.py --bin-dir <Vivado bin directory> --output
<fresh directory>` for a bounded model-free counter verification run.
It preserves source snapshots and hashes, checks simulation and mutation
qualification, then runs synthesis/implementation and records metrics.
Separate launcher/license/toolchain failures from RTL failures.

Next repairs: baseline validation still needs to fail closed (including
missing testbench and infrastructure errors); candidate infra-only rounds
still count as rejects/stalls; restart can still mismatch source and metrics.
Do not start unattended optimization before these are covered by regressions.

Then repair the following in small reviewable changes, adding taxonomy or
curriculum entries and regression coverage as required by CLAUDE.md:

1. Fail closed on simulation/qualification infra errors and ambiguous output.
2. Preserve a matched winning source and metrics across restart/export.
3. Repair build's missing generation method and resume configuration/state.
4. Correct generated testbench latency/scoreboard behavior and interface parsing.
5. Enforce trustworthy metric gates and correct synthesis Tcl/constraints.
6. Demonstrate a counter baseline and verified winner before harder designs.

See the full review for reproductions and remaining findings. No tier has
been newly demonstrated held. Do not merge changes without required gates.
