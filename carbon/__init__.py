"""The main module for carbon."""

from contextlib import suppress
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from carbon.intensity import CarbonIntensity
from carbon.job import Job, JobFactory
from carbon.job.job import EnergyBreakdown
from carbon.node import Node, NodeFactory

with suppress(PackageNotFoundError):
    __version__ = version(__name__)


@dataclass
class RunResult:
    """Structure to hold the results of a carbon calculation run."""

    node: Node
    emissions: float
    energy_consumed: float
    energy_breakdown: EnergyBreakdown
    job: Job
    carbon_intensity: float


def run(
    job_ids: list[str],
    node_factory: NodeFactory,
    job_factory: JobFactory,
    pue: float,
    region_id: int,
    average_intensity: float | None,
    ignore_failed: bool,
) -> list[RunResult]:
    """Estimate the carbon emissions of compute jobs.

    Args:
        job_ids (list[str]): The list of job identifiers to analyze.
        node_factory (NodeFactory): The class used to construct node objects.
        job_factory (JobFactory): The class used to construct job objects.
        pue (float): Power Usage Effectiveness of the data center.
        region_id (int): Region ID for carbon intensity API (1-17)
        average_intensity (float | None): If provided use as the carbon intensity of the
            job instead of calling the CarbonIntensity API.
        ignore_failed (bool): If True, don't crash out when jobs cannot be parsed or
            analysed and don't add respective results to the results list.

    Returns:
        list[RunResult]: The results of the carbon calculations.
    """
    if len(job_ids) > 1:
        arrays = [id for id in job_ids if job_factory.is_array(id)]
        if arrays:
            raise NotImplementedError(
                "Detected multiple array jobs: " + " ".join(arrays) + ". "
                "Analysis of multiple array jobs not implemented. "
                "Please provide a single array job, or a list of jobs/subjobs."
            )
    elif job_factory.is_array(job_ids[0]):
        job_ids = job_factory.split_sub_jobs(job_ids[0])

    job_list = job_factory.create(job_ids, ignore_failed)
    node_list = node_factory.create(
        [job.node for job in job_list],
    )

    result_list = []

    for job, node in zip(job_list, node_list):
        # Calculate energy consumption
        energy_consumed = job.calculate_energy(node, pue)

        # Fetch carbon intensity at job start time or use a provided value
        if average_intensity:
            intensity = average_intensity
        else:
            carbon_intensity = CarbonIntensity(job.starttime, region_id)
            intensity = carbon_intensity.fetch()

        # Calculate emissions
        emissions = intensity * energy_consumed

        result_list.append(
            RunResult(
                node=node,
                emissions=emissions,
                energy_consumed=energy_consumed.total,
                energy_breakdown=energy_consumed,
                job=job,
                carbon_intensity=intensity,
            )
        )

    return result_list
