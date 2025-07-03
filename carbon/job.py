"""The job module.

This module provides functionality for processing and representing a compute job
"""

import json
import subprocess
from datetime import datetime


def hours(time: str) -> float:
    """Convert a time string in HH:MM:SS format to hours."""
    h, m, s = time.split(":")
    return float(h) + float(m) / 60.0 + float(s) / 3600.0


class Job:
    """A class to represent a compute job."""

    def __init__(self, id: str):
        """Initialise a Job object from an ID."""
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

        if output.stdout:
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

            self._id = internal_id
            self._status = job_data["Jobs"][internal_id]["job_state"]
            self._starttime = datetime.strptime(
                job_data["Jobs"][internal_id]["stime"], "%a %b %d %H:%M:%S %Y"
            )

            self._runtime = hours(resources_used["walltime"])
            self._cpuusage = float(resources_used["cpupercent"]) / 100.0
            self._cputime = hours(resources_used["cput"])
            self._ncores = int(resources_used["ncpus"])

            # Allocated memory in kilobytes
            # Allocated memory is more relevant for energy consumption.
            # From DOI:10.1002/advs.202100707
            mem = resources_allocated["mem"]
            if mem.endswith("gb"):
                self._memory = int(mem[:-2])
            else:
                raise NotImplementedError(
                    f"Memory format '{mem}' not implemented. "
                    "Expected format is 'Xgb' where X is an integer."
                )
