"""Unit tests for the Job class and hours conversion."""

import json
import subprocess
from datetime import datetime
from unittest.mock import Mock, patch

import numpy as np
import pytest

from carbon.job import Job, UnknownJobIDError, hours
from carbon.node import Node


def _make_PBSjob_json(internal_id: str = "12345", mpijob: bool = False) -> bytes:
    """Provide a minimal qstat JSON payload as bytes."""
    node_name = "cx3-3-0/60" if not mpijob else "cx3-3-1/60+cx3-3-2/60"

    job_data = {
        "Jobs": {
            internal_id: {
                "job_state": "F",
                "stime": "Wed Jul 09 12:00:00 2025",
                "exec_host": node_name,
                "resources_used": {"walltime": "02:00:00", "cput": "04:00:00"},
                "Resource_List": {"mem": "12gb", "ngpus": "1"},
            }
        }
    }
    return json.dumps(job_data).encode()


def test_from_PBS_bulk_ignore_failed_true(monkeypatch) -> None:
    """Ensure partial stdout from qstat is parsed when ignore_failed is True."""
    # partial_bytes = json.dumps(_partial_job_json()).encode()

    def fake_run(
        cmd, shell, check, timeout, capture_output
    ) -> subprocess.CalledProcessError:
        # Simulate qstat returning exit code 153 (unknown job), but writing
        # valid JSON for some jobs to stdout.
        e = subprocess.CalledProcessError(153, cmd)
        e.stdout = _make_PBSjob_json("123")
        e.stderr = b"Unknown job ID: 456"
        raise e

    monkeypatch.setattr(subprocess, "run", fake_run)

    jobs = Job.from_PBS_bulk(["123", "456"], ignore_failed=True)
    assert len(jobs) == 1
    assert jobs[0].id == "123"


def test_from_PBS_bulk_ignore_failed_false_raises(monkeypatch) -> None:
    """Verify an error is raised when ignore_failed is False and qstat fails."""
    # partial_bytes = json.dumps(_partial_job_json()).encode()

    def fake_run(
        cmd, shell, check, timeout, capture_output
    ) -> subprocess.CalledProcessError:
        e = subprocess.CalledProcessError(153, cmd)
        e.stdout = _make_PBSjob_json("123")
        e.stderr = b"Unknown job ID: 456"
        raise e

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(UnknownJobIDError):
        Job.from_PBS_bulk(["123", "456"], ignore_failed=False)


@pytest.mark.parametrize(
    "isMPIjob, first_node_name",
    [(False, "cx3-3-0"), (True, "cx3-3-1")],
)
def test_fromPBS_parse_job(isMPIjob: bool, first_node_name: str) -> None:
    """Job.fromPBS parses qstat JSON and returns a Job with expected fields."""
    mock_proc = Mock()
    mock_proc.stdout = _make_PBSjob_json("12345", isMPIjob)

    with patch("carbon.job.subprocess.run", return_value=mock_proc):
        job = Job.from_PBS("12345")
    assert job.id == "12345"
    assert job.starttime == datetime.strptime(
        "Wed Jul 09 12:00:00 2025", "%a %b %d %H:%M:%S %Y"
    )
    assert job.runtime == 2.0
    assert job.cputime == 4.0
    assert job.gputime == 2.0
    assert job.memtime == 24.0
    # For MPI jobs, the first node in the list is taken
    assert job.node == first_node_name


def test_hours_conversion() -> None:
    """Test conversion of time string to hours."""
    assert hours("01:30:00") == 1.5
    assert hours("00:45:00") == 0.75
    assert hours("10:00:00") == 10.0


def test_job_init() -> None:
    """Test Job initialization."""
    job = Job(
        id="12345",
        starttime=datetime(2025, 8, 21, 10, 0, 0),
        runtime=2.0,
        cputime=4.0,
        gputime=2.0,
        memtime=64.0,
        node="node01",
    )
    assert job.id == "12345"
    assert job.starttime == datetime(2025, 8, 21, 10, 0, 0)
    assert job.runtime == 2.0
    assert job.cputime == 4.0
    assert job.gputime == 2.0
    assert job.memtime == 64.0
    assert job.node == "node01"


def test_energy_calculate() -> None:
    """Test energy calculation with GPU."""
    job = Job(
        id="12345",
        starttime=datetime(2025, 8, 21, 10, 0, 0),
        runtime=2.0,
        cputime=2.0,
        gputime=2.0,
        memtime=32.0,
        node="node01",
    )
    node = Node(
        name="node01",
        cpu_type="test_cpu",
        gpu_type="test_gpu",
        mem_type="test_mem",
        per_core_power_watts=10.0,
        per_gpu_power_watts=200.0,
        per_gb_power_watts=2.0,
    )

    expected = ((10.0 * 2.0) + (200.0 * 2.0) + (32.0 * 2.0)) * 1.5 / 1000.0
    result = job.calculate_energy(node, 1.5)

    assert np.isclose(result, expected, atol=1e-9)


def test_energy_calculate_no_gpu() -> None:
    """Test energy calculation with GPU."""
    job = Job(
        id="12345",
        starttime=datetime(2025, 8, 21, 10, 0, 0),
        runtime=2.0,
        cputime=2.0,
        gputime=0.0,
        memtime=32.0,
        node="node01",
    )
    node = Node(
        name="node01",
        cpu_type="test_cpu",
        gpu_type=None,
        mem_type="test_mem",
        per_core_power_watts=10.0,
        per_gpu_power_watts=0.0,
        per_gb_power_watts=2.0,
    )

    expected = ((10.0 * 2.0) + (32.0 * 2.0)) * 1.5 / 1000.0
    result = job.calculate_energy(node, 1.5)

    assert np.isclose(result, expected, atol=1e-9)
