"""Unit tests for the exporters."""

import csv
from datetime import datetime
from pathlib import Path

from carbon import RunResult
from carbon.exporter import CSVExporter
from carbon.job import Job
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
    energy_breakdown = EnergyBreakdown(cpu=0.5, gpu=0.0, memory=0.5, total=1.0)
    return RunResult(
        node=node,
        emissions=1.0,
        energy_breakdown=energy_breakdown,
        job=job,
        carbon_intensity=137.0,
    )


def test_csv_exporter_write_rows(tmp_path) -> None:
    """Test that CSVExporter writes rows to a CSV file."""
    output_path = tmp_path / "test_output.csv"
    exporter = CSVExporter(output_path)
    exporter.export([make_result("job1"), make_result("job2")])

    with open(output_path) as csvfile:
        rows = list(csv.DictReader(csvfile))

    assert len(rows) == 2
    assert list(rows[0].keys()) == [
        "job_id",
        "starttime",
        "runtime",
        "cputime",
        "gputime",
        "memtime",
        "node",
        "energy_breakdown_total_kwh",
        "carbon_intensity",
        "emissions",
    ]
    assert rows[0]["job_id"] == "job1"
    assert rows[1]["job_id"] == "job2"


def test_csv_exporter_from_config(tmp_path) -> None:
    """Test that CSVExporter can be created from configuration."""
    output_file = tmp_path / "config_output.csv"
    exporter = CSVExporter.from_config({"output_path": str(output_file)})
    assert exporter.output_path == output_file


def test_csv_exporter_default_output_path() -> None:
    """Test that CSVExporter uses default output path if not specified."""
    exporter = CSVExporter.from_config({})
    assert exporter.output_path == Path("carbon_output.csv")
