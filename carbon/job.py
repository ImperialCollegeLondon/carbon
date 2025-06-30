"""The job module.

This module provides functionality for processing and representing a compute job
"""

import json
import subprocess


class Job:
    """A class to represent a compute job."""

    def __init__(self, id: str):
        """Initialise a Job object from an ID."""
        # cmd = f"qstat -xfF json {id}"
        try:
            output = subprocess.run(
                ["qstat", "-xfF", "json", id],
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

            print(job_data)

            # self._id = None
            # self._status = None
            # self._starttime = None
            # self._runtime = None
            # self._cpuusage = None # Average CPU usage
            # self._cputime = None # Total CPU time in seconds
            # self._ncores = None # Number of CPU cores used
            # self._memory = None
            # self._vmemory = None
