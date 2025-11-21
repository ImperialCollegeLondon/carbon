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


def run(
    job_ids: list[str],
    config: ClusterConfig,
    default_intensity: bool,
    ignore_failed: bool,
) -> list[RunResult]:
    """Estimate the carbon emissions of compute jobs.

    Args:
        job_ids (list[str]): The list of job identifiers to analyze.
        config (ClusterConfig): The cluster configuration.
        default_intensity (bool): If True, use a default carbon intensity value.
        ignore_failed (bool): If True, don't crash out when jobs cannot be parsed or
            analysed and don't add respective results to the results list.

    Returns:
        list[RunResult]: The results of the carbon calculations.
    """
    if len(job_ids) > 1:
        arrays = [id for id in job_ids if Job.is_array(id)]
        if arrays:
            raise NotImplementedError(
                "Detected multiple array jobs: " + " ".join(arrays) + ". "
                "Analysis of multiple array jobs not implemented. "
                "Please provide a single array job, or a list of jobs/subjobs."
            )
    elif Job.is_array(job_ids[0]):
        job_ids = Job.split_sub_jobs(job_ids[0])

    if config.dummy_job:
        # Use dummy job data for testing
        # If multiple ids provided, just duplicate the dummy job
        dummy = config.dummy_job
        dummy_job = Job(
            id="dummy_job",
            starttime=dummy.start_time,
            runtime=dummy.run_time,
            cpurequest=dummy.ncpus,
            gpurequest=dummy.ngpus,
            memrequest=int(dummy.memory),
            cputime=dummy.cpu_time,
            gputime=dummy.ngpus * dummy.run_time,
            memtime=dummy.memory * dummy.run_time,
            node=dummy.node,
        )
        dummy_node = Node(
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
        job_list = [dummy_job] * len(job_ids)
        node_list = [dummy_node] * len(job_ids)
    else:
        job_list = Job.from_PBS(job_ids, ignore_failed)
        node_list = Node.from_PBS(
            [job.node for job in job_list],
            {
                "cpus": config.cpus,
                "gpus": config.gpus,
                "memory": config.memory,
            },
        )

    result_list = []

    for job, node in zip(job_list, node_list):
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

    return result_list
