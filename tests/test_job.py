"""Unit tests for the Job class and hours conversion."""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import numpy as np

from carbon.job import Job, hours
from carbon.node import Node


def _make_PBSjob_json(internal_id: str = "12345") -> bytes:
    """Construct a minimal qstat JSON payload as bytes."""
    job_data = {
        "Jobs": {
            internal_id: {
                "job_state": "F",
                "stime": "Wed Jul 09 12:00:00 2025",
                # exec_host containing two hosts; code will pick the first before '/'
                "exec_host": "cx3-3-0/0",
                "resources_used": {"walltime": "02:00:00", "cput": "04:00:00"},
                "Resource_List": {"mem": "12gb", "ngpus": "1"},
            }
        }
    }
    return json.dumps(job_data).encode()


def test_fromPBS_parse_job() -> None:
    """Job.fromPBS parses qstat JSON and returns a Job with expected fields."""
    mock_proc = Mock()
    mock_proc.stdout = _make_PBSjob_json("12345")

    with patch("carbon.job.subprocess.run", return_value=mock_proc):
        job = Job.fromPBS("12345")
    assert job.id == "12345"
    assert job.starttime == datetime.strptime(
        "Wed Jul 09 12:00:00 2025", "%a %b %d %H:%M:%S %Y"
    )
    assert job.runtime == 2.0
    assert job.cputime == 4.0
    assert job.memory == 12.0
    assert job.ngpus == 1
    assert job.node == "cx3-3-0"


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
        ngpus=2,
        memory=32.0,
        node="node01",
    )
    assert job.id == "12345"
    assert job.starttime == datetime(2025, 8, 21, 10, 0, 0)
    assert job.runtime == 2.0
    assert job.cputime == 4.0
    assert job.ngpus == 2
    assert job.memory == 32.0
    assert job.node == "node01"


def test_energy_calculate() -> None:
    """Test energy calculation with GPU."""
    job = Job(
        id="12345",
        starttime=datetime(2025, 8, 21, 10, 0, 0),
        runtime=2.0,
        cputime=2.0,
        ngpus=1,
        memory=16.0,
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

    expected = ((10.0 * 2.0) + (200.0 * 1 * 2.0) + (2.0 * 16.0 * 2.0)) * 1.5 / 1000.0
    result = job.calculate_energy(node, 1.5)

    assert np.isclose(result, expected, atol=1e-9)


def test_energy_calculate_no_gpu() -> None:
    """Test energy calculation with GPU."""
    job = Job(
        id="12345",
        starttime=datetime(2025, 8, 21, 10, 0, 0),
        runtime=2.0,
        cputime=2.0,
        ngpus=0,
        memory=16.0,
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

    expected = ((10.0 * 2.0) + (2.0 * 16.0 * 2.0)) * 1.5 / 1000.0
    result = job.calculate_energy(node, 1.5)

    assert np.isclose(result, expected, atol=1e-9)
