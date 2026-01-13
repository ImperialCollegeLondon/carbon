"""Integration tests for the CLI/main behaviour using the dummy config."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from carbon.__main__ import main


@pytest.fixture(autouse=True)
def fetch_mock(mocker) -> MagicMock:
    """Patch CarbonIntensity.fetch to avoid real API calls in tests."""
    return mocker.patch("carbon.intensity.CarbonIntensity.fetch", return_value=1.0)


def test_single_job() -> None:
    """A single-job run with --average-intensity prints usable details."""
    cfg_path = str(Path(__file__).parents[1] / "clusters" / "dummy.yaml")

    runner = CliRunner()
    res = runner.invoke(
        main, ["--config-path", cfg_path, "--average-intensity", "1234"]
    )
    assert res.exit_code == 0
    out = res.output
    assert "Job run on node: dummy_node" in out
    # average-intensity flag should trigger the average intensity message
    assert "Using average carbon intensity of 100.0 gCO2/kWh" in out
    assert (
        "Estimated energy consumed from 192.00 CPU-hours "
        "and 24.00 GPU-hours and 288.00 GB-hours is 10.22 kWh" in out
    )
    assert "Estimated emissions is 1022 gCO2" in out


def test_multiple_jobs_aggregate() -> None:
    """Multiple jobs without --split_jobs produce an aggregate block."""
    cfg_path = str(Path(__file__).parents[1] / "clusters" / "dummy.yaml")

    runner = CliRunner()
    res = runner.invoke(
        main, ["--config-path", cfg_path, "--average-intensity", "1234", "5678"]
    )
    assert res.exit_code == 0
    out = res.output
    assert "Aggregating estimates over multiple jobs." in out
    assert (
        "Estimated energy consumed from 384.00 CPU-hours "
        "and 48.00 GPU-hours and 576.00 GB-hours is 20.44 kWh" in out
    )
    assert "Estimated emissions is 2044 gCO2" in out


def test_multiple_jobs_split_results() -> None:
    """Multiple jobs with --split_jobs print a block per job."""
    cfg_path = str(Path(__file__).parents[1] / "clusters" / "dummy.yaml")

    runner = CliRunner()
    job_ids = ["1234", "5678"]
    res = runner.invoke(
        main,
        [
            "--config-path",
            cfg_path,
            "--average-intensity",
            "--split-jobs",
            *job_ids,
        ],
    )
    assert res.exit_code == 0
    out = res.output
    # Ensure we get output for each job
    for job_id in job_ids:
        assert f"Job ID: {job_id}" in out
    assert (
        out.count(
            "Estimated energy consumed from 192.00 CPU-hours "
            "and 24.00 GPU-hours and 288.00 GB-hours is 10.22 kWh"
        )
        == 2
    )
    assert out.count("Estimated emissions is 1022 gCO2") == 2


def test_intensity_api(fetch_mock) -> None:
    """A single-job run without --average-intensity prints usable details."""
    cfg_path = str(Path(__file__).parents[1] / "clusters" / "dummy.yaml")

    runner = CliRunner()
    res = runner.invoke(main, ["--config-path", cfg_path, "1234"])
    assert res.exit_code == 0
    fetch_mock.assert_called_once()

    out = res.output
    assert (
        "Estimated energy consumed from 192.00 CPU-hours "
        "and 24.00 GPU-hours and 288.00 GB-hours is 10.22 kWh"
    ) in out
    assert "Estimated emissions is 10 gCO2" in out
