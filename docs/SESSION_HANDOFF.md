# Session handoff

Updated: 2026-10-16 (America/New_York)

## Objective and decisions

Build a reliable autonomous RTL improvement loop, starting with small
designs and increasing complexity only after demonstrated correctness.
Keep evidence suitable for the owner's CV. Use command-line Vivado now;
MCP is deferred. No background schedule is configured.
User replaced all previous model providers with Codex-only workers, supervised
by the main development agent. Parallel development helpers are authorized.

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
- Current checkpoint includes Codex CLI adapter/routing, fail-closed baseline,
  restart winner preservation, finite timing metrics, tool process-tree cleanup,
  and supervised counter generation trial. Inspect git status before continuing.

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
- Latest full suite: 226 tests passed in 9.10 seconds on 2026-10-16.
- Actual Codex generator call succeeded using existing ChatGPT login (model
  identifier not reported). Counter RTL passed initial simulation and stuck-zero
  mutation check. Trial01 implementation timed out at 300 seconds; old driver
  left a Vivado child alive. Parent verified its command line and stopped it.
- Repaired driver kills the owned process tree and preserves partial diagnostics.
  Replay trial02 passed with the same RTL and stronger synchronous-reset tests.
  6 LUTs, 8 FFs, WNS 7.806 ns, WHS 0.249 ns at 10 ns on xc7a35tcpg236-1.
  It made no new model call; raw kind field still says generation but explicit
  source_import metadata identifies replay. New code corrects this label.
- Timing Doctor isolated-trial and cache metric-gate repairs passed independent
  review and integrated tests. Valid cache hits still lack original report
  provenance. No held-tier or optimization-improvement claim.

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

Next repairs: candidate infra-only rounds still count as rejects/stalls;
cache keys still omit full context; resume and build remain incomplete.
Baseline validation and restart winner preservation
are now covered by regression tests. Do not start unattended optimization yet.

Then repair the following in small reviewable changes, adding taxonomy or
curriculum entries and regression coverage as required by CLAUDE.md:

1. Finish cache context/provenance and infrastructure round accounting.
2. Repair resume configuration/checkpoints and build's missing generation method.
3. Correct generated testbench latency/scoreboard behavior and interface parsing.
4. Demonstrate bounded Codex-driven optimization with trustworthy comparisons.
5. Progress counter -> mux -> priority encoder, then stateful/protocol designs.

See the full review for reproductions and remaining findings. No tier has
been newly demonstrated held. Do not merge changes without required gates.
