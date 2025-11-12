"""Integration tests for the CLI/main behaviour using the dummy config.

These tests exercise the CLI entrypoint without mocking by relying on the
repository's `clusters/dummy.yaml` which provides a `dummy_job` fixture for
deterministic output. Tests use `--default_intensity` to avoid external API
calls and ensure repeatable numbers.
"""

from pathlib import Path

from click.testing import CliRunner

from carbon.__main__ import main


def test_single_job() -> None:
    """A single-job run with --default_intensity prints usable details."""
    cfg_path = str(Path(__file__).parents[1] / "clusters" / "dummy.yaml")

    runner = CliRunner()
    res = runner.invoke(
        main, ["--config_path", cfg_path, "--default_intensity", "1234"]
    )
    assert res.exit_code == 0
    out = res.output
    assert "Job run on node: dummy_node" in out
    # default_intensity should trigger the UK-average intensity message
    assert "Using UK average carbon intensity of 137.0 gCO2/kWh" in out
    assert (
        "Estimated energy consumed from 192.00 CPU-hours "
        "and 24.00 GPU-hours and 288.00 GB-hours is 10.22 kWh" in out
    )
    assert "Estimated emissions is 1400 gCO2" in out


def test_multiple_jobs_aggregate() -> None:
    """Multiple jobs without --split_jobs produce an aggregate block."""
    cfg_path = str(Path(__file__).parents[1] / "clusters" / "dummy.yaml")

    runner = CliRunner()
    res = runner.invoke(
        main, ["--config_path", cfg_path, "--default_intensity", "1234", "5678"]
    )
    assert res.exit_code == 0
    out = res.output
    assert "Aggregating estimates over multiple jobs." in out
    assert (
        "Estimated energy consumed from 384.00 CPU-hours "
        "and 48.00 GPU-hours and 576.00 GB-hours is 20.44 kWh" in out
    )
    assert "Estimated emissions is 2801 gCO2" in out


def test_multiple_jobs_split_results() -> None:
    """Multiple jobs with --split_jobs print a block per job."""
    cfg_path = str(Path(__file__).parents[1] / "clusters" / "dummy.yaml")

    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "--config_path",
            cfg_path,
            "--default_intensity",
            "--split_jobs",
            "1234",
            "5678",
        ],
    )
    assert res.exit_code == 0
    out = res.output
    # The dummy job id is used for each entry; ensure exactly two blocks printed
    assert out.count("Job ID: dummy_job") == 2
    assert (
        out.count(
            "Estimated energy consumed from 192.00 CPU-hours "
            "and 24.00 GPU-hours and 288.00 GB-hours is 10.22 kWh"
        )
        == 2
    )
    assert out.count("Estimated emissions is 1400 gCO2") == 2
