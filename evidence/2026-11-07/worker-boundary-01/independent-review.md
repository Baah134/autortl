# Independent review: restricted text-generation worker

Reviewed isolated `work/nov7-worker-boundary-stage/llm/backends/codex_cli.py`, the
new boundary tests, modified existing backend tests, current installed-CLI
inspection/help, real configuration-list/feature-state receipts and taxonomy
proposal. No canonical edits, model requests, vendor jobs or board actions were
performed. This review did not repeat the full regression.

## Verdict

The change is suitable for the stated configured-worker scope, subject to one
small deadline correction below and the documented default-configuration
semantics. No additional agent/framework, environment rewrite or hypothetical
new-capability discovery is required for this pinned CLI experiment.

### Concrete correction: check the deadline before starting generation

At the reviewed `ask()` implementation, `_remaining(deadline)` is called for
`communicate()` **after** `subprocess.Popen`. If the final configuration probe
or its result validation exhausts the deadline, generation is still launched
and then cancelled. That can begin a request despite an already-expired budget.

`work/nov7-boundary-review-probe.py` reproduces this with a mocked preflight
that advances the shared monotonic clock past its deadline. The actual result
is CODEX_TIMEOUT, but `Popen` was called and cleanup followed. No real process
was started by the probe. Receipt: `work/nov7-boundary-deadline-probe.json`.

Minimal correction: call `_remaining(deadline)` immediately before `Popen` and
keep the existing remaining-time calculation for `communicate()`. Add a test
where preflight finishes after the deadline and assert `Popen` is never called.
This is a known-expiry guard, not a claim that clock checks and OS process
creation are atomic.

## Correctness and evidence

- MCP discovery and enforcement are separate. Empty-map inheritance was
  reproduced; named inert disabled entries plus a second effective inventory
  address it. Newly appearing/managed enabled entries in that second inventory
  block execution. Inert commands prevent retaining the user's transport in
  generated policy, and enabled=false prevents normal startup. Names are TOML
  data via JSON basic-string quoting; control/surrogate/duplicate/oversize
  validation and an injection-shaped-name regression are meaningful.
- The installed CLI's model-free receipt shows all ten explicitly disabled
  feature states false and node_repl disabled. This is stronger evidence than
  asserting argv strings alone. The ten flags are also supplied to the final
  worker. No authentication, CODEX_HOME, managed permission, network or tool-pipe
  environment is rewritten; exec rules are not bypassed.
- Unsupported flags/configuration, malformed inventories and enabled servers
  fail without a weaker retry. Inventory output/transports are not copied into
  error text. The new failure messages are constant, and existing prompt/token
  redaction remains in the worker-error path. Quota/auth/network classification
  remains in the existing event/nonzero-exit handling.
- Preflight and generation share the original deadline. Configuration queries
  have their own ten-second caps; actual generation timeout/cancellation still
  cleans only the owned tree through the existing implementation. A CLI
  configuration-list timeout has no model/server initialization in the reviewed
  command. The deadline guard above closes the one observed launch-order gap.
- Only the known textual item types are accepted. Tool/unknown events reject a
  nonempty final answer, and a completed-turn event cannot override that
  rejection. This is post-execution validation; it cannot undo a side effect.
  Current tests correctly describe this limitation rather than claiming mocks
  prove an OS sandbox.

The focused tests exercise actual adapter control flow with mocks: inventory
before worker, effective enabled-server refusal, parsing/error/byte limits,
quoting, timeout sharing, unchanged environment, public-adapter rejection and
strict textual-item acceptance. Existing lifecycle/error tests remain relevant.
They do not establish the runtime's full model-facing tool catalog; the real
configuration receipt does not make that claim either.

## Compatibility and documentation conditions

`exec --ignore-user-config` intentionally stops loading the user's config.toml,
while retaining their authentication home. A pinned model argument remains
pinned. An omitted/default alias now uses the CLI's builtin/default selection
rather than the user's config.toml model/provider/reasoning/service preferences.
Document that behavior next to setup/model selection; do not continue promising
that runtime workers inherit all personal Codex settings. Model/backend observed
identity and unknown cost/token fields must remain accurately distinguished.

The preflight itself still reads effective configuration to discover injected
servers. A malformed/incompatible inherited config can therefore block preflight
even though the final worker ignores the user file. That is conservative refusal,
not a reason to silently skip the check or rewrite global configuration.

For this frozen run, the tested CLI0.166.0-alpha.6 executable hash and real
disabled-feature receipt provide adequate evidence for the ten named controls.
An additional per-call `features list` query is not an integration blocker;
it would recheck the same current flags while still not revealing an entire
runtime tool catalog or unknown future features. Preserve the executable hash
and receipts and repeat compatibility qualification when the CLI changes.
Unsupported versions/configs should remain blocked; do not claim support for
every future CLI merely because strict parsing accepts its arguments.

The proposed success metadata (`worker_policy: restricted_text_v1`,
`mcp_configuration_checked: true`, `tool_items_observed: 0`) is appropriate if
added only after successful preflight/event validation. It records what this
policy checked and observed; it must not be named or described as universal
physical/device isolation. A harmless live generation control remains a
separate measured step, not something the mock/config-only receipts establish.
