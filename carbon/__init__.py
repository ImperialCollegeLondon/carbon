"""The main module for carbon."""

from contextlib import suppress
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from carbon.clusterconfig import ClusterConfig
from carbon.intensity import CarbonIntensity
from carbon.job import Job, UnsupportedJobType
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


def run(job_id: str, config: ClusterConfig) -> RunResult:
    """Estimate the carbon emissions of a compute job.

    Args:
        job_id (str): The job identifier to analyze.
        config (ClusterConfig): The cluster configuration.

    Returns:
        RunResult: The results of the carbon calculation.
    """
    # Get the job data and node hardware info
    if config.dummy_job:
        # Use dummy job data for testing
        dummy = config.dummy_job
        job = Job(
            job_id,
            dummy.start_time,
            dummy.run_time,
            dummy.cpu_time,
            dummy.ngpus,
            dummy.memory_usage,
            dummy.node,
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
        # Remove suffix to make IDs more uniform
        id = job_id.split(".")[0]

        if id.endswith("[]"):
            raise UnsupportedJobType("array")

        # Fetch job data from the cluster's job scheduler
        job = Job.fromPBS(id)
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

    # Fetch carbon intensity at job startime time
    carbon_intensity = CarbonIntensity(job.starttime)
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
