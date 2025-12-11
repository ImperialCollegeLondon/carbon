"""Unit tests for the command-line interface."""

from datetime import datetime
from pathlib import Path

from click.testing import CliRunner

from carbon import RunResult
from carbon.__main__ import main
from carbon.job import Job, JobState
from carbon.node import Node


def make_result(job_id: str) -> RunResult:
    """Construct a synthetic RunResult for tests using the given job ID.

    The returned RunResult contains a Job and Node with deterministic values
    suitable for asserting CLI output.
    """
    job = Job(
        id=job_id,
        starttime=datetime(2025, 10, 26, 23, 43, 39),
        runtime=1.0,
        cputime=100.0,
        gputime=0.0,
        memtime=100.0,
        node="cx3-1-1",
        state=JobState.FINISHED,
    )
    node = Node(
        name="cx3-1-1",
        cpu_type="x",
        gpu_type=None,
        mem_type="m",
        per_core_power_watts=1.0,
        per_gpu_power_watts=0.0,
        per_gb_power_watts=0.5,
    )
    return RunResult(
        node=node, emissions=1.0, energy_consumed=1.0, job=job, carbon_intensity=137.0
    )


def test_cli_split_jobs_prints_each(monkeypatch) -> None:
    """When --split_jobs is given, ensure the CLI prints a block per job.

    Monkeypatches the internal run() call to return deterministic results and
    asserts that each job's ID appears in the CLI output.
    """
    cfg_path = str(Path(__file__).parents[1] / "clusters" / "dummy.yaml")

    def fake_run(
        job_ids,
        node_factory,
        job_factory,
        pue,
        region_id,
        average_intensity,
        ignore_failed,
    ) -> list[RunResult]:
        return [make_result("jobA"), make_result("jobB")]

    # Patch the run function used by the CLI module
    monkeypatch.setattr("carbon.__main__.run", fake_run)

    runner = CliRunner()
    # Ensure options (config) come before positional args to avoid parsing issues
    res = runner.invoke(
        main, ["--config-path", cfg_path, "--split-jobs", "jobA", "jobB"]
    )
    assert res.exit_code == 0
    out = res.output
    assert "Job ID: jobA" in out
    assert "Job ID: jobB" in out


def test_cli_aggregate_prints_aggregate(monkeypatch) -> None:
    """When multiple jobs are requested without --split_jobs, print aggregate.

    Verifies the CLI prints aggregation messages and an estimated energy
    summary for multiple jobs.
    """
    cfg_path = str(Path(__file__).parents[1] / "clusters" / "dummy.yaml")
    results = [make_result("jobA"), make_result("jobB")]

    def fake_run(
        job_ids,
        node_factory,
        job_factory,
        pue,
        region_id,
        average_intensity,
        ignore_failed,
    ) -> list[RunResult]:
        return results

    monkeypatch.setattr("carbon.__main__.run", fake_run)

    runner = CliRunner()
    res = runner.invoke(main, ["--config-path", cfg_path, "jobA", "jobB"])
    assert res.exit_code == 0
    out = res.output
    assert "Aggregating estimates over multiple jobs." in out
    assert "Estimated energy consumed" in out
