# Restrict the configured Codex text worker

Status: isolated proposal. Canonical repository, user configuration, credentials and board untouched. No model turn, MCP server initialization, vendor job, hardware-manager action, JTAG or serial operation was invoked. Root owns canonical integration, taxonomy, full regressions and any later live control.

Use **proposal-v3.patch / receipt-v3.json** for integration. Original **proposal.patch**, **proposal-v1.patch**, **receipt.json**, **receipt-v1.json**, **v1-source/**, **proposal-v2.patch**, **receipt-v2.json**, **v2-source/** and all before/failure logs remain preserved. V2 added successful-response policy metadata and the MCP parser fixture. V3 closes the independently reproduced late-deadline spawn bug. The final patch has five paths: backend, existing backend tests, new boundary tests, unexpected-tool JSONL fixture, MCP-inventory JSON fixture. `taxonomy-entry.yaml` is a separate draft for the required pre-fix failure-mode entry.

Final patch SHA256: `b43446fdca1c331cd8d7722ca10445d44b025ffda061ef7b0fd15f1bd49977c1`.

## Observed problem and smallest justified change

The existing adapter says not to use tools but inherits local configuration. Its event parser accepts tool trajectories. A read-only filesystem sandbox does not make MCP tools read-only. This matters with the user's FPGA connected: a model-only role should not inherit arbitrary host integrations.

Official OpenAI documentation supports ignoring user configuration while retaining existing authentication, strict configuration validation, capability settings and per-server disablement. The installed CLI has no documented universal no-tools flag. See [CLI reference](https://learn.chatgpt.com/docs/cli/reference), [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference), [MCP configuration](https://learn.chatgpt.com/docs/extend/mcp), and [configuration schema](https://developers.openai.com/codex/config-schema.json). Documentation was searched and opened before local CLI inspection, following the OpenAI Docs skill.

Installed CLI inspection: **0.166.0-alpha.6**, executable SHA256 `925c7d0665ffa49b0dcf748e034a805a04da984164ac92301432073b47789b99`. Help confirms `--ignore-user-config`, `--strict-config`, `--disable`, and `--config`. The explicit feature names were checked against this CLI and the official schema rather than guessed.

The proposal:

1. Run workers with `--ignore-user-config --strict-config`, retaining the existing read-only sandbox, login, environment and explicit model argument. Disable shell execution, apps, local image viewing, hooks, plugins, native multi-agent delegation, code mode, computer use, browser use and image generation; disable web search separately. Do not bypass approvals, hooks or execpolicy rules.
2. Before a model turn, list MCP configuration without initializing servers. Discover names, replace entries with complete disabled entries using an inert nonexistent command, then require the effective inventory to have **no enabled server**. Never copy the user's actual command, URL, arguments, environment or credentials into the replacement entries or diagnostics.
3. Share one monotonic `timeout_s` deadline across the two inventory calls and worker communication, checking remaining time immediately before process creation. Each inventory also has a10-second ceiling within the remaining deadline. Reject malformed inventory, missing/non-boolean enabled states, duplicates, oversized names/counts and accepted output beyond256KiB. No fallback retries with weaker settings.
4. Reject non-text/unknown JSONL items and unknown event types even if a final response and completed turn exist. Successful responses record `worker_policy=restricted_text_v1`, `mcp_configuration_checked=true`, `tool_items_observed=0`. These state the configured policy and observed/checked facts; `max_turns_enforced` remains false and requested/observed model handling stays unchanged.

This adds a bounded configuration check to the existing adapter, not a new agent framework or a universal security sandbox.

## Actual model-free diagnosis

`cli-inspection.json`, `transport-probe.json`, `disabled-entry-probe.json` and `profile-validation.json` retain sanitized results:

- Baseline configured integrations included enabled `cua_repl` and `node_repl`.
- An empty `mcp_servers` map plus plugin/app/capability disables still left `node_repl` enabled.
- A partial `.enabled=false` override failed bootstrap transport validation on this installation.
- A complete disabled entry with an inert command passed validation and reported the server disabled. No real transport was copied.
- Parent authorized a child-only A/B probe removing just two suspected tool-transport environment variables. It did not remove the residual integration. The proposal therefore **does not strip environment variables**. Auth, permission profile, sandbox/network settings and global environment remain unchanged.
- The staged production preflight itself was run model-free: discovery reported `node_repl=true`, validation reported `node_repl=false`. A separate local feature listing with the same overrides confirmed all ten capability features false. No model call was made.

These observations establish the practical configuration restriction for this installed CLI and configuration. They do not establish all possible future tool registrations.

## Tests and retained failures

Final exact commands and SHA256 identities are in `receipt-v3.json`. The focused suite includes all21 existing Codex backend tests plus46 boundary tests. The final baseline uses the original byte-preserved backend with the final tests/fixtures and valid mocked inventories; only failing tests caused by the actual boundary gap are counted. The existing cleanup/cancellation/process-tree assertions remain in place.

- Initial `before-tests.txt`: default pytest temp location was inaccessible; its11 setup errors are infrastructure and are not boundary evidence.
- `before-tests-workspace-temp.txt`: clean-temp original backend36failed/1passed on the initial regression set.
- `after-tests.txt`: first combined run56passed/2failed because an old cleanup test replaced the inventory mock with an unspecified Mock. This was a test adaptation failure, preserved rather than relabelled.
- `before-v3-tests.txt`: final V1 original backend44failed/22passed; `after-v3-tests.txt`:66passed.
- `before-v4-tests.txt` / `after-v4-tests.txt`: final V2 with metadata and parser fixture, summarized in receipt-v2.
- `deadline-before-tests.txt`: independent-review follow-up reproduced an expired configuration check still spawning a worker under V2 (1failed/45deselected, all process actions mocked). V3 checks the shared deadline immediately before Popen.
- **Final V3:** `before-v5-tests.txt`:45failed/22passed in2.91s against the original backend; `after-v5-tests.txt`:**67passed in1.91s**. No regression test or mock calls a real model, server or hardware tool.

Tests cover preflight ordering before worker launch, preservation of security/auth environment, no weakening retry, MCP-policy TOML quoting, invalid inventories and byte/count bounds, one shared deadline, unsupported CLI settings, timeout cleanup compatibility, and rejection of command/MCP/file/web/delegation/unknown items even beside a usable final answer. `codex_unexpected_tool.jsonl` is a synthetic event control; its contents are never executed. `codex_mcp_inventory.json` is a synthetic configuration-parser fixture, not a hardware connection.

## Semantics and remaining limits

- **User model/provider defaults change.** Ignoring user configuration means an unspecified/default model now uses the CLI's built-in defaults, not the user's configured profile/provider. An explicit `--model` request is preserved; it does not restore a custom user provider. Existing authentication is reused without reading, copying or printing credential files. Users needing a custom endpoint should use AutoRTL's explicit endpoint backend. This behavior needs user documentation when integrated.
- **No universal pre-execution guarantee.** The CLI does not expose a supported complete model-facing tool allowlist through this adapter. An MCP configuration listing is not the complete runtime tool catalog. Managed policies, future versions, built-ins or configuration races can change behavior. Unknown event shapes fail closed, but that happens after the worker has run.
- **Post-hoc rejection cannot undo effects.** Rejecting a command/tool item prevents accepting its answer, not the action that already occurred. Do not present the JSONL check as a preventive hardware boundary or as proof hidden benchmark graders cannot be read.
- **Not a memory-safe output reader.** The256KiB inventory bound limits accepted configuration results after subprocess capture; it is not a streaming pipe/memory cap. Existing worker output capture likewise remains outside a universal memory-isolation claim.
- **No new safety bypass.** Environment restrictions, managed requirements, authentication and rule loading remain in force. Unsupported CLI/settings or an enabled effective MCP server stop the attempt before generation; no weaker automatic fallback is added.
- **Evidence scope.** No full harness regression, authenticated harmless model sentinel or full runtime-tool-catalog proof was run in this stage. Before a fresh model campaign, root should review/integrate, run the complete software suite and perform any explicitly approved harmless text-only runtime control. Board operations remain deterministic and separately reviewed; this patch does not authorize a model to touch hardware.
