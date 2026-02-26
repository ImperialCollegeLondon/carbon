"""Job factory base class and dummy implementation."""

import json
import re
import subprocess
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, Self

import pydantic
import yaml

from ..clusterconfig import DummySchedulerConfig
from .job import Job, JobState


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


class MissingJobDataError(ValueError):
    """Raised when job data is missing from object returned by scheduler."""

    pass


class JobFactory(Protocol):
    """Abstract base class for job factories."""

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> Self:  # type: ignore[explicit-any]
        """Create an instance of the class from configuration data."""

    @abstractmethod
    def is_array(self, job_id: str) -> bool:
        """Check if the job ID corresponds to an array job.

        Args:
            job_id (str): The job ID to check.

        Returns:
            bool: True if the job ID is for an array job, False otherwise.
        """

    @abstractmethod
    def split_sub_jobs(self, job_id: str) -> list[str]:
        """Split an array job ID into its sub-job IDs.

        Args:
            job_id (str): The array job ID to split.

        Returns:
            list[str]: A list of sub-job IDs.
        """

    @abstractmethod
    def create(cls, job_ids: list[str], ignore_failed: bool = False) -> list[Job]:
        """Create multiple Job instances from a list of job IDs.

        Args:
            job_ids (list[str]): A list of job IDs.
            ignore_failed (bool): Whether to ignore failed job creations.
        """


@dataclass
class DummyJobFactory(JobFactory):
    """A dummy job factory for demonstration purposes."""

    start_time: datetime
    run_time: float
    cpu_time: float
    ngpus: int
    memory_usage: float
    node: str

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Self:  # type: ignore[explicit-any]
        """Initialize from configuration data."""
        validated_config = DummySchedulerConfig(**config)
        return cls(
            start_time=validated_config.start_time,
            run_time=validated_config.run_time,
            cpu_time=validated_config.cpu_time,
            ngpus=validated_config.ngpus,
            memory_usage=validated_config.memory_usage,
            node=validated_config.node,
        )

    def is_array(self, job_id: str) -> bool:
        """Check if the job ID corresponds to an array job.

        For dummy purposes array jobs are not supported.
        """
        return False

    def split_sub_jobs(self, job_id: str) -> list[str]:
        """Return the sub-job IDs for an array job.

        Raises NotImplementedError as array jobs are not supported.
        """
        raise NotImplementedError("Array jobs are not supported in DummyJobFactory.")

    def create(self, job_ids: list[str], ignore_failed: bool = False) -> list[Job]:
        """Create dummy Job instances for the given job IDs.

        Args:
            job_ids (list[str]): The job identifiers to create.
            ignore_failed (bool): Ignored in this dummy implementation.
        """
        return [
            Job(
                id=job_id,
                starttime=self.start_time,
                runtime=self.run_time,
                cputime=self.cpu_time,
                gputime=self.ngpus * self.run_time,
                memtime=self.memory_usage * self.run_time,
                node=self.node,
            )
            for job_id in job_ids
        ]


def hours(time: str) -> float:
    """Convert a time string in HH:MM:SS format to hours.

    Args:
        time (str): Time string in the format 'HH:MM:SS'.

    Returns:
        float: The time in hours.
    """
    h, m, s = time.split(":")
    return float(h) + float(m) / 60.0 + float(s) / 3600.0


PBS_JOB_ID_RE = re.compile(r"^\d+(\[\d+\])?(?:..*)?$")
PBS_SUBJOB_ID_RE = re.compile(r"^\d+\[\d+\](?:..*)?$")
PBS_ARRAY_ID_RE = re.compile(r"^\d+\[\](?:..*)?$")

PBS_UNKNOWN_JOB_EXIT_CODE = 153
PBS_MALFORMED_JOB_EXIT_CODES = {1, 170}
PBS_KNOWN_EXIT_CODES = PBS_MALFORMED_JOB_EXIT_CODES | {PBS_UNKNOWN_JOB_EXIT_CODE}


@dataclass
class PBSJobFactory(JobFactory):
    """A job factory for PBS scheduler."""

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Self:  # type: ignore[explicit-any]
        """Initialize the PBS job factory."""
        return cls()

    def is_array(self, job_id: str) -> bool:
        """Check if the job ID corresponds to an array job."""
        return job_id.split(".")[0].endswith("[]")

    def split_sub_jobs(self, job_id: str) -> list[str]:
        """Split a PBS array job id into the corresponding list of subjob ids."""
        # Job ID for array should be digits followed by square brackets
        if not PBS_ARRAY_ID_RE.fullmatch(job_id):
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
            if e.returncode == PBS_UNKNOWN_JOB_EXIT_CODE:
                raise UnknownJobIDError(f"Unknown job ID: {job_id}")
            elif e.returncode in PBS_MALFORMED_JOB_EXIT_CODES:
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
            if PBS_SUBJOB_ID_RE.fullmatch(label) and state in JobState:
                # Add subjobs without server label to improve consistency
                sub_jobs.append(label.split(".")[0])

        return sub_jobs

    def create(self, job_ids: list[str], ignore_failed: bool = False) -> list[Job]:
        """Create a list of Job objects by fetching data from PBS for multiple job IDs.

        Args:
            job_ids (list[str]): The job identifiers to fetch from the scheduler.
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
            MissingJobDataError: If expected job data is missing.
        """
        malformed_ids = []
        for id in job_ids:
            if not PBS_JOB_ID_RE.fullmatch(id):
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
            job_ids = [id for id in job_ids if id not in malformed_ids]

        if not job_ids:
            return []

        cmd = "qstat -xfF json " + " ".join(job_ids)

        # Placeholder for storing partial stdout if subprocess raises and ignore_failed
        # is True.
        e_stdout = b""

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

            if e.returncode in PBS_KNOWN_EXIT_CODES:
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
                    if e.returncode == PBS_UNKNOWN_JOB_EXIT_CODE:
                        raise UnknownJobIDError(f"Unknown job ID(s): {bad_ids}")
                    elif e.returncode in PBS_MALFORMED_JOB_EXIT_CODES:
                        raise MalformedJobIDError(f"Malformed job ID(s): {bad_ids}")
            else:
                raise

        stdout = output.stdout if not e_stdout else e_stdout
        job_data = json.loads(stdout)

        if not job_data or "Jobs" not in job_data.keys():
            raise MissingJobDataError(f"No job data found for ID(s): {job_ids}")

        job_list = []
        for internal_id in job_data["Jobs"]:
            try:
                state = job_data["Jobs"][internal_id]["job_state"]
                if state not in JobState:
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
                    Job(
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
                    raise MissingJobDataError(f"Missing expected job data: {e}")
        return job_list


class FileJobFactory(JobFactory):
    """A job factory that reads job data from YAML files."""

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> Self:  # type: ignore[explicit-any]
        """Initialize the File job factory."""
        # no config used currently
        return cls()

    def is_array(self, job_id: str) -> bool:
        """Check if the job ID corresponds to an array job.

        For file-based jobs array jobs are not supported.
        """
        return False

    def split_sub_jobs(self, job_id: str) -> list[str]:
        """Return the sub-job IDs for an array job.

        Raises NotImplementedError as array jobs are not supported.
        """
        raise NotImplementedError("Array jobs are not supported in FileJobFactory.")

    class FileJobModel(pydantic.BaseModel):
        """Pydantic model for file-based job data."""

        model_config = pydantic.ConfigDict(use_enum_values=True)

        id: str
        starttime: datetime
        runtime_hours: float
        cputime_corehours: float
        ngpus: int
        memory_gb: float
        node: str
        state: JobState

    def create(self, job_ids: list[str], ignore_failed: bool = False) -> list[Job]:
        """Create Job instances from YAML files.

        Args:
            job_ids (list[str]): Interpreted as file paths to YAML files.
            ignore_failed (bool): Ignored in this implementation.

        Returns:
            list[Job]: A list of Job instances created from the files.
        """
        jobs = []
        for job_id in job_ids:
            with open(job_id) as f:
                job_data = self.FileJobModel(**yaml.safe_load(f))
            jobs.append(
                Job(
                    id=job_data.id,
                    starttime=job_data.starttime,
                    runtime=job_data.runtime_hours,
                    cputime=job_data.cputime_corehours,
                    gputime=job_data.ngpus * job_data.runtime_hours,
                    memtime=job_data.memory_gb * job_data.runtime_hours,
                    node=job_data.node,
                    state=job_data.state,
                )
            )
        return jobs
