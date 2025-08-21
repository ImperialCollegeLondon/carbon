"""Unit tests for the Job class and hours conversion."""

from datetime import datetime

from carbon.job import Job, hours


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
