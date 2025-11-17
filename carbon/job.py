"""The job module.

This module provides functionality for processing and representing a compute job,
including parsing job data from a scheduler, converting time formats, and calculating
the electrical energy consumed by the job.
"""

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Self

from carbon.node import Node

# Pre-compile regular expressions for performance.
# These patterns are used during job id validation.
JOB_ID_RE = re.compile(r"^\d+(\[\d+\])?(?:..*)?$")
SUBJOB_ID_RE = re.compile(r"^\d+\[\d+\](?:..*)?$")
ARRAY_ID_RE = re.compile(r"^\d+\[\](?:..*)?$")


class UnknownJobIDError(ValueError):
    """Raised for unknown job IDs."""

    pass


class MalformedJobIDError(ValueError):
    """Raised for illegally formed job IDs."""

    pass


class JobStateError(ValueError):
    """Raised for jobs in an invalid state."""

    pass


class UnsupportedJobType(ValueError):
    """Raised for job types that are not supported."""

    def __init__(self, job_type: str) -> None:
        """Initialize the UnsupportedJobType exception.

        Args:
            job_type (str): The unsupported job type.
        """
        super().__init__(f"Unsupported job type: {job_type}")
        self.job_type = job_type


class MissingJobData(ValueError):
    """Raised when job data is missing from object returned by scheduler."""

    pass


class JobState(Enum):
    """Enumeration of supported job states."""

    FINISHED = "F"
    RUNNING = "R"
    EXPIRED = "X"


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

    gputime: float
    """The total GPU time used by the job in component-hours."""

    memtime: float
    """The total memory-time allocated to the job in GB-hours."""

    node: str
    """The node the job was executed on."""

    state: JobState = JobState.FINISHED
    """The state of the job."""

    @classmethod
    def is_array(cls, job_id: str) -> bool:
        """Is it a PBS array job?"""
        return job_id.split(".")[0].endswith("[]")

    @classmethod
    def split_sub_jobs(cls, job_id: str) -> list[str]:
        """Split a PBS array job id into the corresponding list of subjob ids."""
        # Job ID for array should be digits followed by square brackets
        if not ARRAY_ID_RE.fullmatch(job_id):
            raise MalformedJobIDError(
                f"Malformed array job ID: {job_id}. Should contain only digits, "
                "followed by square brackets"
            )

        # Use -J and -t flags to output a table of array subjobs
        cmd = f"qstat -xJt {job_id}"

        try:
            output = subprocess.run(
                cmd,
                shell=True,
                check=True,
                timeout=20,
                capture_output=True,
                text=True,  # Potentially a 10000 line long str. Could improve?
            )
        except subprocess.CalledProcessError as e:
            if e.returncode == 153:
                raise UnknownJobIDError(f"Unknown job ID: {job_id}")
            elif e.returncode == 1 or e.returncode == 170:
                raise MalformedJobIDError(f"Malformed job ID: {job_id}")
            else:
                raise ValueError(f"Failed to fetch job data: {e}")

        sub_jobs = []
        for row in output.stdout.splitlines()[3:]:
            items = row.split()
            label = items[0]
            state = items[4]
            # Get all the subjobs which are running, finished, or expired (finished but
            # other subjobs are still running).
            if SUBJOB_ID_RE.fullmatch(label) and state in [
                "R",
                "F",
                "X",
            ]:
                # Add subjobs without server label to improve consistency
                sub_jobs.append(label.split(".")[0])

        return sub_jobs

    @classmethod
    def from_PBS_bulk(cls, ids: list[str], ignore_failed: bool = False) -> list[Self]:
        """Create a list of Job objects by fetching data from PBS for multiple job IDs.

        Args:
            ids (list[str]): The job identifiers to fetch from the scheduler.
            ignore_failed (bool): If True, don't crash out when jobs cannot be parsed
                but don't add to the job list.

        Returns:
            list[Job]: A list containing instances of the Job class corresponding to
                each of the ids.

        Raises:
            ValueError: If fetching or parsing job data fails, or if no job data is
                found.
            UnknownJobIDError: If PBS returns exit code 153 for unknown job ID.
            MalformedJobIDError: If some of the job IDs are not formatted correctly.
            JobStateError: If some of the jobs are in an invalid state.
            NotImplementedError: If the memory format is not supported.
        """
        malformed_ids = []
        for id in ids:
            if not JOB_ID_RE.fullmatch(id):
                malformed_ids.append(id)
        if malformed_ids and not ignore_failed:
            raise MalformedJobIDError(
                "Malformed job ID(s): " + " ".join(malformed_ids) + ". "
                "Should be composed of digits, "
                "optionally followed by an index in square brackets, "
                "optionally followed by a full stop and the PBS server name."
            )
        elif malformed_ids and ignore_failed:
            # Remove malformed ids from the list of ids
            ids = [id for id in ids if id not in malformed_ids]

        if not ids:
            return []

        cmd = "qstat -xfF json " + " ".join(ids)

        # Placeholder for storing partial stdout if subprocess raises and ignore_failed
        # is True.
        e_stdout: bytes | None = None

        try:
            output = subprocess.run(
                cmd,
                shell=True,
                check=True,
                timeout=20,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            # PBS may return a non-zero exit code while still printing valid JSON
            # to stdout for the jobs it could find. If ignore_failed is True,
            # attempt to parse e.stdout and continue with the valid jobs. If not,
            # raise the appropriate exception.

            if e.returncode in [153, 1, 170]:
                # Try to extract the list of bad ids from stderr if present
                bad_ids = " ".join(
                    [
                        line.split()[-1]
                        for line in str(e.stderr, "utf-8").splitlines()
                        if line.strip()
                    ]
                )

                # If the caller asked us to ignore failed ids, and there is
                # partial JSON output on stdout, parse that and continue.
                if ignore_failed:
                    e_stdout = e.stdout
                else:
                    if e.returncode == 153:
                        raise UnknownJobIDError(f"Unknown job ID(s): {bad_ids}")
                    elif e.returncode == 1 or e.returncode == 170:
                        raise MalformedJobIDError(f"Malformed job ID(s): {bad_ids}")
            else:
                raise

        stdout = output.stdout if not e_stdout else e_stdout
        job_data = json.loads(stdout)

        if not job_data or "Jobs" not in job_data.keys():
            raise MissingJobData(f"No job data found for ID(s): {ids}")

        job_list = []
        for internal_id in job_data["Jobs"]:
            try:
                state = job_data["Jobs"][internal_id]["job_state"]
                if state not in ["F", "R", "X"]:
                    if ignore_failed:
                        continue
                    else:
                        raise JobStateError(
                            f"Analysis of jobs with state {state} is not "
                            "currently supported. Please specify a running (R), "
                            "finished (F), or expired (X) job."
                        )

                # If the job ran on multiple nodes (e.g., using MPI),
                # just take the first one. This will be used to get the cpu_type
                # and gpu_type, which should be the same across the nodes.
                nodes = [
                    name.split("/", 1)[0]
                    for name in job_data["Jobs"][internal_id]["exec_host"].split("+")
                ]
                node = nodes[0]
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
                elif ignore_failed:
                    continue
                else:
                    raise NotImplementedError(
                        f"Memory format '{_memory}' not implemented. "
                        "Expected format is 'Xgb' where X is an integer."
                    )

                runtime = hours(resources_used["walltime"])

                # Create a Job object with the fetched data
                # and append to the job_list
                job_list.append(
                    cls(
                        id=internal_id,
                        starttime=starttime,
                        runtime=runtime,
                        cputime=hours(resources_used["cput"]),
                        gputime=int(resources_allocated["ngpus"]) * runtime,
                        memtime=memory * runtime,
                        node=node,
                        state=JobState(state),
                    )
                )
            except KeyError as e:
                if ignore_failed:
                    continue
                else:
                    raise ValueError(f"Missing expected job data: {e}")
        return job_list

    @classmethod
    def from_PBS(cls, id: str) -> Self:
        """Create a single Job object by fetching data from PBS based on the job ID.

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
        jobs = cls.from_PBS_bulk([id])
        return jobs[0]

    def calculate_energy(self, node: Node, pue: float) -> float:
        """Calculate energy consumption in kilowatt-hours for a compute job.

        Args:
            node (Node): The compute node the job was executed on.
            pue (float): Power Usage Effectiveness of the data center.

        Returns:
            float: The energy consumed in kilowatt-hours.
        """
        return (
            (
                node.per_core_power_watts * self.cputime
                + node.per_gpu_power_watts * self.gputime
                + node.per_gb_power_watts * self.memtime
            )
            * pue
            / 1000.0
        )
