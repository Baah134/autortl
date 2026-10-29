"""run.py bench --jobs N runs entries concurrently with the same records and cohort."""
from concurrent.futures import ThreadPoolExecutor

import pytest

from curriculum import runner
from tests.test_curriculum import curriculum, records  # noqa: F401  (fixture reuse)


def test_parallel_entries_give_the_same_records_and_cohort(curriculum, monkeypatch):  # noqa: F811
    _, orch, output = curriculum
    assert runner.run_tier(0, output_root=output) == 0
    monkeypatch.setattr(runner, "EXECUTOR", ThreadPoolExecutor)  # processes cannot see the mocked Orchestrator
    assert runner.run_tier(0, output_root=output, jobs=3) == 0
    sequential, parallel = records()
    assert [r["entry"] for r in parallel["results"]] == [r["entry"] for r in sequential["results"]] == list("abcde")
    assert parallel["cohort"] == sequential["cohort"]
    assert parallel["consecutive_qualifying_runs"] == 2
    assert orch.call_count == 10


def test_a_crashing_parallel_entry_is_an_exception_record(curriculum, monkeypatch):  # noqa: F811
    _, orch, output = curriculum
    construct = orch.side_effect

    def build(cfg, run_dir):
        if run_dir.name == "c":
            raise RuntimeError("boom")
        return construct(cfg, run_dir)

    orch.side_effect = build
    monkeypatch.setattr(runner, "EXECUTOR", ThreadPoolExecutor)
    # A crash before the run folder exists also leaves its runtime provenance unknown,
    # so the campaign cannot qualify; it is still recorded as an exception.
    assert runner.run_tier(0, output_root=output, jobs=2) == 1
    failed = [r for r in records()[-1]["results"] if not r["ok"]]
    assert [(r["entry"], r["reason"]) for r in failed] == [("c", "RuntimeError: boom")]


@pytest.mark.parametrize("jobs", [0, -1, 1.5, "2"])
def test_jobs_must_be_a_positive_integer(curriculum, jobs):  # noqa: F811
    _, _, output = curriculum
    with pytest.raises(ValueError, match="jobs"):
        runner.run_tier(0, output_root=output, jobs=jobs)


def test_the_real_executor_is_a_process_pool():
    from concurrent.futures import ProcessPoolExecutor
    assert runner.EXECUTOR is ProcessPoolExecutor
