"""Unit tests for the command-line interface."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from click.testing import CliRunner

from carbon import RunResult
from carbon.__main__ import main
from carbon.job import Job, JobState
from carbon.job.job import EnergyBreakdown
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
        node=node,
        emissions=1.0,
        job=job,
        energy_breakdown=EnergyBreakdown(cpu=0, gpu=0, memory=0, total=1.0),
        carbon_intensity=137.0,
    )


@pytest.fixture
def run_mock(mocker) -> MagicMock:
    """Fixture to patch the run() function used by the CLI."""
    return mocker.patch("carbon.__main__.run")


CFG_PATH = Path(__file__).parents[1] / "clusters" / "dummy.yaml"


def test_cli_split_jobs_prints_each(run_mock) -> None:
    """When --split_jobs is given, ensure the CLI prints a block per job.

    Monkeypatches the internal run() call to return deterministic results and
    asserts that each job's ID appears in the CLI output.
    """
    run_mock.return_value = [make_result("jobA"), make_result("jobB")]

    runner = CliRunner()
    # Ensure options (config) come before positional args to avoid parsing issues
    res = runner.invoke(
        main, ["--config-path", str(CFG_PATH), "--split-jobs", "jobA", "jobB"]
    )
    assert res.exit_code == 0
    out = res.output
    assert "Job ID: jobA" in out
    assert "Job ID: jobB" in out


def test_cli_aggregate_prints_aggregate(run_mock) -> None:
    """When multiple jobs are requested without --split_jobs, print aggregate.

    Verifies the CLI prints aggregation messages and an estimated energy
    summary for multiple jobs.
    """
    results = [make_result("jobA"), make_result("jobB")]
    run_mock.return_value = results
    runner = CliRunner()
    res = runner.invoke(main, ["--config-path", str(CFG_PATH), "jobA", "jobB"])
    assert res.exit_code == 0
    out = res.output
    assert "Aggregating estimates over multiple jobs." in out
    assert "Estimated energy consumed" in out


def test_exporter_config(tmp_path, mocker) -> None:
    """Test that the CLI passes exporter options from config file."""
    mod_cfg_path = tmp_path / "test_config.yaml"
    output_path = tmp_path / "test_output.csv"

    # write new config file with exporter options
    with open(CFG_PATH) as f:
        config_data = yaml.safe_load(f)
    config_data["exporters"] = ["csv"]
    config_data["exporter_config"] = dict(csv=dict(output_path=str(output_path)))
    with open(mod_cfg_path, "w") as f:
        yaml.safe_dump(config_data, f)

    exporter_mock = MagicMock()
    mocker.patch(
        "carbon.__main__.get_exporter_classes", return_value=dict(csv=exporter_mock)
    )
    results = [make_result("jobA")]
    mocker.patch("carbon.__main__.run", return_value=results)
    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "--config-path",
            mod_cfg_path,
            f"path={output_path}",
            "jobA",
        ],
    )
    assert res.exit_code == 0
    exporter_mock.from_config.assert_called_once_with({"output_path": str(output_path)})
    exporter_mock.from_config().export.assert_called_once_with(results)
