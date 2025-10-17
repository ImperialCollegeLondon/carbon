"""The job module.

This module provides functionality for processing and representing a compute job,
including parsing job data from a scheduler and converting time formats.
"""

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Self


class UnknownJobIDError(ValueError):
    """Raised for unknown job IDs."""

    pass


class MalformedJobIDError(ValueError):
    """Raised for illegally formed job IDs."""

    pass


class JobStateError(ValueError):
    """Raised for jobs in an invalid state."""

    pass


def hours(time: str) -> float:
    """Convert a time string in HH:MM:SS format to hours.

    Args:
        time (str): Time string in the format 'HH:MM:SS'.

    Returns:
        float: The time in hours.
    """
    h, m, s = time.split(":")
    return float(h) + float(m) / 60.0 + float(s) / 3600.0


@dataclass
class Job:
    """Represents a compute job, including its resource usage and timing information."""

    id: str
    """The job identifier."""

    starttime: datetime
    """The start time of the job."""

    runtime: float
    """The total runtime of the job in hours."""

    cputime: float
    """The total CPU time used by the job in core-hours."""

    ngpus: int
    """The number of GPUs used by the job."""

    memory: float
    """The memory allocated to the job in GB."""

    node: str
    """The node the job was executed on."""

    @classmethod
    def fromPBS(cls, id: str) -> Self:
        """Create a Job object by fetching data from PBS based on the job ID.

        Args:
            id (str): The job identifier to fetch from the scheduler.

        Returns:
            Job: An instance of the Job class populated with scheduler data.

        Raises:
            ValueError: If fetching or parsing job data fails, or if no job data is
                found.
            UnknownJobIDError: If PBS returns exit code 153 for unknown job ID.
            MalformedJobIDError: If the job ID is not formatted correctly.
            JobStateError: If the job is in an invalid state.
            NotImplementedError: If the memory format is not supported.
        """
        # Job ID should either be digits only or digits plus an index in square brackets
        if not re.fullmatch(r"\d+(\[\d+\])?", id):
            raise MalformedJobIDError(
                f"Malformed job ID: {id}. Should contain only digits"
            )

        cmd = f"qstat -xfF json {id}"

        try:
            output = subprocess.run(
                cmd,
                shell=True,
                check=True,
                timeout=10,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            if e.returncode == 153:
                raise UnknownJobIDError(f"Unknown job ID: {id}")
            elif e.returncode == 1 or e.returncode == 170:
                raise MalformedJobIDError(f"Malformed job ID: {id}")
            else:
                raise ValueError(f"Failed to fetch job data: {e}")

        try:
            job_data = json.loads(output.stdout)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse job data: {e}")
        if not job_data:
            raise ValueError(f"No job data found for ID {id}")

        # Get the job ID as recorded by the job scheduler.
        # Here we assume only one job was captured by qstat.
        # If multiple jobs are returned, this will only return the first one.
        internal_id = next(iter(job_data["Jobs"]))
        state = job_data["Jobs"][internal_id]["job_state"]
        if not (state == "F" or state == "R"):
            raise JobStateError(
                f"Analysis of jobs with state {state} is not "
                "currently supported. Please specify a running (R) or "
                "finished (F) job."
            )

        if state == "R":
            print(
                f"Job {internal_id} is currently running. Note that energy and "
                "emissions estimates will be for only the completed portion of the job "
                "and may not reflect total emissions."
            )

        node = job_data["Jobs"][internal_id]["exec_host"].split("/", 1)[0]
        resources_used = job_data["Jobs"][internal_id]["resources_used"]
        resources_allocated = job_data["Jobs"][internal_id]["Resource_List"]

        # Process some of the job data.
        starttime = datetime.strptime(
            job_data["Jobs"][internal_id]["stime"], "%a %b %d %H:%M:%S %Y"
        )
        # Allocated memory in gb.
        # Allocated memory is more relevant for energy consumption.
        # From DOI:10.1002/advs.202100707
        _memory = resources_allocated["mem"]
        if _memory.endswith("gb"):
            memory = float(_memory[:-2])
        else:
            raise NotImplementedError(
                f"Memory format '{_memory}' not implemented. "
                "Expected format is 'Xgb' where X is an integer."
            )

        # Create a Job object with the fetched data
        return cls(
            id=internal_id,
            starttime=starttime,
            runtime=hours(resources_used["walltime"]),
            cputime=hours(resources_used["cput"]),
            memory=memory,
            ngpus=int(resources_allocated["ngpus"]),
            node=node,
        )
