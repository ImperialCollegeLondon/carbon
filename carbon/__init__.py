"""The main module for carbon."""

from contextlib import suppress
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from carbon.clusterconfig import ClusterConfig
from carbon.intensity import CarbonIntensity
from carbon.job import Job
from carbon.node import Node

with suppress(PackageNotFoundError):
    __version__ = version(__name__)


@dataclass
class RunResult:
    """Structure to hold the results of a carbon calculation run."""

    node: Node
    emissions: float
    energy_consumed: float
    job: Job
    carbon_intensity: float


def run_single(
    job_id: str, config: ClusterConfig, default_intensity: bool, ignore_failed: bool
) -> RunResult:
    """Estimate the carbon emissions of a compute job.

    Args:
        job_id (str): The job identifier to analyze.
        config (ClusterConfig): The cluster configuration.
        default_intensity (bool): If True, use a default carbon intensity value.
        ignore_failed (bool): If True, don't crash out when job cannot be parsed or
            analysed.

    Returns:
        RunResult: The results of the carbon calculation.
    """
    if ignore_failed:
        raise NotImplementedError(
            "ignore_failed not compatible with analysis of single jobs."
        )

    # Get the job data and node hardware info
    if config.dummy_job:
        # Use dummy job data for testing
        dummy = config.dummy_job
        job = Job(
            id=job_id,
            starttime=dummy.start_time,
            runtime=dummy.run_time,
            cputime=dummy.cpu_time,
            gputime=dummy.ngpus * dummy.run_time,
            memtime=dummy.memory_usage * dummy.run_time,
            node=dummy.node,
        )
        node = Node(
            name=dummy.node,
            cpu_type=dummy.cpu_type,
            gpu_type=dummy.gpu_type,
            mem_type=dummy.mem_type,
            per_core_power_watts=config.cpus[dummy.cpu_type]["per_core_power_watts"],
            per_gpu_power_watts=config.gpus[dummy.gpu_type]["per_gpu_power_watts"]
            if dummy.gpu_type
            else 0.0,
            per_gb_power_watts=config.memory[dummy.mem_type]["per_gb_power_watts"],
        )
    else:
        # Fetch job data from the cluster's job scheduler
        job = Job.from_PBS(job_id)
        node = Node.from_PBS(
            job.node,
            {
                "cpus": config.cpus,
                "gpus": config.gpus,
                "memory": config.memory,
            },
        )
    # Calculate energy consumption
    energy_consumed = job.calculate_energy(node, config.pue)

    # Fetch carbon intensity at job start time or use a default value
    if default_intensity:
        intensity = 137.0  # gCO2/kWh, UK average over 2023 and 2024
    else:
        carbon_intensity = CarbonIntensity(job.starttime, config.region_id)
        intensity = carbon_intensity.fetch()

    # Calculate emissions
    emissions = intensity * energy_consumed
    return RunResult(
        node=node,
        emissions=emissions,
        energy_consumed=energy_consumed,
        job=job,
        carbon_intensity=intensity,
    )


def run_multiple(
    job_id_list: list[str],
    config: ClusterConfig,
    default_intensity: bool,
    ignore_failed: bool,
) -> tuple[list[RunResult], int]:
    """Estimate the carbon emissions of multiple compute jobs.

    Args:
        job_id_list (list[str]): The list of job identifiers to analyze.
        config (ClusterConfig): The cluster configuration.
        default_intensity (bool): If True, use a default carbon intensity value.
        ignore_failed (bool): If True, don't crash out when jobs cannot be parsed or
            analysed and don't add respective results to the results list.

    Returns:
        tuple[list[RunResult], int]: The results of the carbon calculations, plus an
            integer count of failed analyses.
    """
    result_list = []

    job_list = Job.from_PBS_bulk(job_id_list, ignore_failed)

    for job in job_list:
        node = Node.from_PBS(
            job.node,
            {
                "cpus": config.cpus,
                "gpus": config.gpus,
                "memory": config.memory,
            },
        )

        # Calculate energy consumption
        energy_consumed = job.calculate_energy(node, config.pue)

        # Fetch carbon intensity at job start time or use a default value
        if default_intensity:
            intensity = 137.0  # gCO2/kWh, UK average over 2023 and 2024
        else:
            carbon_intensity = CarbonIntensity(job.starttime, config.region_id)
            intensity = carbon_intensity.fetch()

        # Calculate emissions
        emissions = intensity * energy_consumed

        result_list.append(
            RunResult(
                node=node,
                emissions=emissions,
                energy_consumed=energy_consumed,
                job=job,
                carbon_intensity=intensity,
            )
        )

    return result_list, len(job_id_list) - len(result_list)


def run(
    job_ids: tuple[str, ...],
    config: ClusterConfig,
    default_intensity: bool,
    ignore_failed: bool,
) -> tuple[list[RunResult], int]:
    """Select between analysis of a single, multiple, or array job.

    Args:
        job_ids (str): The job identifier(s) to analyze.
        config (ClusterConfig): The cluster configuration.
        default_intensity (bool): If True, use a default carbon intensity value.
        ignore_failed (bool): If True, don't crash out when jobs cannot be parsed or
            analysed and don't add respective results to the results list.

    Returns:
        tuple[list[RunResult], int]: The results of the carbon calculations, plus an
            integer count of failed analyses.
    """
    if len(job_ids) == 1:
        if Job.is_array(job_ids[0]):
            job_id_list = Job.split_sub_jobs(job_ids[0])
            return run_multiple(job_id_list, config, default_intensity, ignore_failed)
        else:
            return (
                [run_single(job_ids[0], config, default_intensity, ignore_failed)],
                0,
            )
    else:
        arrays = [id for id in job_ids if Job.is_array(id)]
        if arrays:
            raise NotImplementedError(
                "Detected multiple array jobs: " + " ".join(arrays) + ". "
                "Analysis of multiple array jobs not implemented. "
                "Please provide a single array job, or a list of jobs/subjobs."
            )

        return run_multiple(list(job_ids), config, default_intensity, ignore_failed)
