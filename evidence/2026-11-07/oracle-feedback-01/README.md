# Oracle module-boundary clarification

Oracle clarification validation: 2078 passed in 518.77s (0:08:38); 323 passed, 1 skipped in 59.24s; 341 frozen inputs unchanged.
Only generic module-boundary and top-level-helper instructions changed; no
roles/FSM/sandbox/budget changes. AES01 remains a failed oracle build, with
three rejected attempts and no new hardware or curriculum verdict. The next
fresh run is AES02 on the published correction with original limits.

The failed AES controller models recomputed neighboring logic and ignored
provided round_out/key_next values. A restricted-worker diagnosis reproduced
all failures. Its handwritten diagnostic control is not generated-design
success and was not supplied to production generation.

The prompt now describes authoritative input values and supported top-level
helpers, explicitly permitting legitimately unused inputs. Before1failed/3passed;
95focused tests passed after. Independent review approved unchanged semantics
and policy. Public-example/source-feedback expansion remains conditional on
the simpler measured trial. No LLM improvement is inferred from these tests.
