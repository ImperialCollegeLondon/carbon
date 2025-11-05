"""The main module for carbon."""

from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
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
    job_id: str, config: ClusterConfig, default_intensity: bool = False
) -> RunResult:
    """Estimate the carbon emissions of a compute job.

    Args:
        job_id (str): The job identifier to analyze.
        config (ClusterConfig): The cluster configuration.
        default_intensity (bool): If True, use a default carbon intensity value.

    Returns:
        RunResult: The results of the carbon calculation.
    """
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
            isaggregate=False,
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
        job = Job.fromPBS(job_id)
        node = Node.fromPBS(
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
        carbon_intensity = CarbonIntensity(job.starttime, region_id=config.region_id)
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
    job_id_list: list[str], config: ClusterConfig, default_intensity: bool = False
) -> RunResult:
    """Estimate the carbon emissions of multiple compute jobs.

    Args:
        job_id_list (list[str]): The list of job identifiers to analyze.
        config (ClusterConfig): The cluster configuration.
        default_intensity (bool): If True, use a default carbon intensity value.

    Returns:
        RunResult: The results of the carbon calculation.
    """
    job_list = []
    node_list = []

    earliest_startime = datetime.max
    total_runtime = 0.0
    total_cputime = 0.0
    total_gputime = 0.0
    total_memtime = 0.0

    total_energy_consumed = 0.0
    total_emissions = 0.0
    average_carbon_intensity: float

    for i, job_id in enumerate(job_id_list):
        single_result = run_single(job_id, config, default_intensity)

        job_list.append(single_result.job)
        node_list.append(single_result.node)

        if single_result.job.starttime < earliest_startime:
            earliest_startime = single_result.job.starttime
        total_runtime += single_result.job.runtime
        total_cputime += single_result.job.cputime
        total_gputime += single_result.job.gputime
        total_memtime += single_result.job.memtime

        total_energy_consumed += single_result.energy_consumed
        total_emissions += single_result.emissions
        if i == 0:
            average_carbon_intensity = single_result.carbon_intensity
        else:
            # Update moving average
            average_carbon_intensity = average_carbon_intensity * i / (
                i + 1
            ) + single_result.carbon_intensity / (i + 1)

    # If all jobs ran on the same node, use that label, otherwise use "Multiple"
    # For now, just report the specs from the first node
    agg_node = node_list[0]
    if not node_list.count(node_list[0]) == len(node_list):
        agg_node.name = "Multiple"

    # Create an aggregate job which holds resource usage totals
    agg_job = Job(
        id="Aggregate",
        starttime=earliest_startime,
        runtime=total_runtime,
        cputime=total_cputime,
        gputime=total_gputime,
        memtime=total_memtime,
        node=agg_node.name,
        isaggregate=True,
    )

    return RunResult(
        node=agg_node,
        emissions=total_emissions,
        energy_consumed=total_energy_consumed,
        job=agg_job,
        carbon_intensity=average_carbon_intensity,
    )


def run(
    job_id: str, config: ClusterConfig, default_intensity: bool = False
) -> RunResult:
    """Select between analysis of a single or array job.

    Args:
        job_id (str): The job identifier to analyze.
        config (ClusterConfig): The cluster configuration.
        default_intensity (bool): If True, use a default carbon intensity value.

    Returns:
        RunResult: The results of the carbon calculation.
    """
    if Job.is_array(job_id):
        job_id_list = Job.split_sub_jobs(job_id)
        return run_multiple(job_id_list, config, default_intensity)
    else:
        return run_single(job_id, config, default_intensity)
