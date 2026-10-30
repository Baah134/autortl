"""Two benches at once never drop a curriculum record.

Taxonomy: concurrent_bench_drops_history, cross_tier_benches_serialized.
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


def _tier1_line():
    record = {"tier": 1, "cohort": "other-tier", "qualified": True, "held": False, "full_tier": True,
              "consecutive_qualifying_runs": 1, "results": [{"entry": "x", "ok": True}]}
    return (json.dumps(record) + "\n").encode()


def _during_next_campaign(orch, change):
    construct = orch.side_effect

    def other_bench_finishes_meanwhile(cfg, run_dir):
        if not getattr(other_bench_finishes_meanwhile, "done", False):
            other_bench_finishes_meanwhile.done = True
            change()
        return construct(cfg, run_dir)

    orch.side_effect = other_bench_finishes_meanwhile


def test_another_tier_finishing_during_a_campaign_is_kept(curriculum):  # noqa: F811
    # cross_tier_benches_serialized
    _, orch, output = curriculum
    assert runner.run_tier(0, output_root=output) == 0
    before = runner.RESULTS.read_bytes()
    _during_next_campaign(orch, lambda: runner.RESULTS.write_bytes(before + _tier1_line()))
    assert runner.run_tier(0, output_root=output) == 0
    after = runner.RESULTS.read_bytes()
    assert after.startswith(before + _tier1_line())  # earlier bytes never re-serialized
    assert [r["tier"] for r in records()] == [0, 1, 0]
    assert runner.run_tier(0, output_root=output) == 0
    tier0 = [r for r in records() if r["tier"] == 0]
    assert [r["consecutive_qualifying_runs"] for r in tier0] == [1, 2, 3] and tier0[-1]["held"]
    assert not runner.RESULTS.with_name(runner.RESULTS.name + ".lock").exists()


def test_the_same_tier_finishing_during_a_campaign_still_fails_closed(curriculum):  # noqa: F811
    _, orch, output = curriculum
    assert runner.run_tier(0, output_root=output) == 0
    before = runner.RESULTS.read_bytes()
    other = before + _tier1_line() + before.splitlines(keepends=True)[-1]
    _during_next_campaign(orch, lambda: runner.RESULTS.write_bytes(other))
    assert runner.run_tier(0, output_root=output) == 3
    assert runner.RESULTS.read_bytes() == other
    assert not runner.RESULTS.with_name(runner.RESULTS.name + ".lock").exists()


def test_a_rewritten_history_still_fails_closed(curriculum):  # noqa: F811
    _, orch, output = curriculum
    assert runner.run_tier(0, output_root=output) == 0
    before = runner.RESULTS.read_bytes()
    rewritten = _tier1_line() + before  # grew, but the start bytes are no longer a prefix
    _during_next_campaign(orch, lambda: runner.RESULTS.write_bytes(rewritten))
    assert runner.run_tier(0, output_root=output) == 3
    assert runner.RESULTS.read_bytes() == rewritten


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


def test_a_stale_lock_is_replaced_but_a_fresh_one_still_blocks(curriculum):  # noqa: F811
    import os, time
    _, _, output = curriculum
    lock = runner.RESULTS.with_name(runner.RESULTS.name + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("")
    old = time.time() - runner.STALE_LOCK_SECONDS - 60
    os.utime(lock, (old, old))
    assert runner.run_tier(0, output_root=output) == 0  # stale_history_lock_blocks_benches
    assert len(records()) == 1 and not lock.exists()


def test_every_entry_records_the_requested_model(curriculum):  # noqa: F811
    _, _, output = curriculum
    assert runner.run_tier(0, output_root=output, model="gpt-6-luna") == 0
    assert {r["runtime_identity"]["model_identity"] for r in records()[-1]["results"]} == {"gpt-6-luna"}
