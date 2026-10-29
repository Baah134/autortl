"""Two benches at once never drop a curriculum record.

Taxonomy: concurrent_bench_drops_history.
"""
import json

from curriculum import runner
from tests.test_curriculum import curriculum, records  # noqa: F401  (fixture reuse)


def test_a_history_change_during_a_campaign_fails_closed(curriculum):  # noqa: F811
    _, orch, output = curriculum
    assert runner.run_tier(0, output_root=output) == 0
    before = runner.RESULTS.read_bytes()
    construct = orch.side_effect

    def other_bench_finishes_meanwhile(cfg, run_dir):
        if not getattr(other_bench_finishes_meanwhile, "done", False):
            other_bench_finishes_meanwhile.done = True
            runner.RESULTS.write_bytes(before + before.splitlines(keepends=True)[-1])
        return construct(cfg, run_dir)

    orch.side_effect = other_bench_finishes_meanwhile
    assert runner.run_tier(0, output_root=output) == 3
    # The other bench's record survives; this campaign's stays in its summary.json.
    assert len(records()) == 2
    summaries = sorted(output.rglob("summary.json"))
    assert len(summaries) == 2 and json.loads(summaries[-1].read_text())["tier"] == 0
    assert not runner.RESULTS.with_name(runner.RESULTS.name + ".lock").exists()


def test_a_held_lock_blocks_the_write(curriculum):  # noqa: F811
    _, _, output = curriculum
    lock = runner.RESULTS.with_name(runner.RESULTS.name + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("")
    assert runner.run_tier(0, output_root=output) == 3
    assert not runner.RESULTS.exists()
    assert lock.exists()  # never removes a lock it did not take


def test_sequential_benches_still_append(curriculum):  # noqa: F811
    _, _, output = curriculum
    for _ in range(3):
        assert runner.run_tier(0, output_root=output) == 0
    assert [r["consecutive_qualifying_runs"] for r in records()] == [1, 2, 3]
