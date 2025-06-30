"""The job module.

This module provides functionality for processing and representing a compute job
"""

import json
import subprocess
from datetime import datetime


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

            self._id = internal_id
            self._status = job_data["Jobs"][internal_id]["job_state"]
            self._starttime = datetime.strptime(
                job_data["Jobs"][internal_id]["stime"], "%a %b %d %H:%M:%S %Y"
            )

            resources = job_data["Jobs"][internal_id]["resources_used"]
            h, m, s = resources["walltime"].split(":")
            self._runtime = float(h) + float(m) / 60.0 + float(s) / 3600.0
            self._cpuusage = float(resources["cpupercent"]) / 100.0  # Average CPU usage
            self._cputime = resources["cput"]  # HH:MM:SS format
            self._ncores = int(resources["ncpus"])  # Number of CPU cores used

            # Memory usage in kilobytes
            mem = resources["mem"]
            if mem.endswith("kb"):
                self._memory = int(mem[:-2])
            else:
                raise NotImplementedError(
                    f"Memory format '{mem}' not implemented. "
                    "Expected format is 'Xkb' where X is an integer."
                )

            # Virtual memory usage in kilobytes
            vmem = resources["vmem"]
            if vmem.endswith("kb"):
                self._vmemory = int(vmem[:-2])
            else:
                raise NotImplementedError(
                    f"Virtual memory format '{vmem}' not implemented. "
                    "Expected format is 'Xkb' where X is an integer."
                )
