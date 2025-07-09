"""The job module.

This module provides functionality for processing and representing a compute job
"""

import json
import subprocess
from datetime import datetime
from typing import Self


def hours(time: str) -> float:
    """Convert a time string in HH:MM:SS format to hours."""
    h, m, s = time.split(":")
    return float(h) + float(m) / 60.0 + float(s) / 3600.0


class Job:
    """A class to represent a compute job."""

    def __init__(
        self,
        id: str,
        starttime: datetime,
        runtime: float,
        cputime: float,
        ngpus: int,
        memory: int,
    ) -> None:
        """Initialise the Job object."""
        self.id = id
        self.starttime = starttime
        self.runtime = runtime
        self.cputime = cputime
        self.ngpus = ngpus
        self.memory = memory

    @classmethod
    def fromResources(
        cls, id: str, runtime: float, cputime: float, ngpus: int, memory: int
    ) -> Self:
        """Create a job object from compute resource data."""
        starttime = datetime.now()  # Use current time as start time for job

        return cls(
            id=id,
            starttime=starttime,
            runtime=runtime,
            cputime=cputime,
            ngpus=ngpus,
            memory=memory,
        )

    @classmethod
    def fromPBS(cls, id: str) -> Self:
        """Create a job object by fetching data from PBS based on the job ID."""
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
        resources_used = job_data["Jobs"][internal_id]["resources_used"]
        resources_allocated = job_data["Jobs"][internal_id]["Resource_List"]

        # Process some of the job data.
        starttime = datetime.strptime(
            job_data["Jobs"][internal_id]["stime"], "%a %b %d %H:%M:%S %Y"
        )
        # Allocated memory in gb.
        # Allocated memory is more relevant for energy consumption.
        # From DOI:10.1002/advs.202100707
        mem = resources_allocated["mem"]
        if mem.endswith("gb"):
            memory = int(mem[:-2])
        else:
            raise NotImplementedError(
                f"Memory format '{mem}' not implemented. "
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
        )
