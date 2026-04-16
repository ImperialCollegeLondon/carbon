"""Configuration schema for an HPC cluster and its power usage characteristics."""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt, PositiveFloat


class DummySchedulerConfig(BaseModel):
    """Optional dummy job specification for testing and development purposes.

    Attributes:
        start_time (datetime): Start time of the job in ISO format.
        cpu_time (float): CPU time used by the job in cpu core-hours.
        memory_usage (float): Memory allocated to the job in GB.
        run_time (float): Total run time of the job in hours.
        ngpus (int): Number of GPUs used by the job.
        node (str): Label of the node the job was executed on.
        cpu_type (str): CPU type for dummy job.
        gpu_type (str | None): GPU type for dummy job, or None if not present.
        mem_type (str): Memory type for dummy job
    """

    start_time: datetime
    cpu_time: NonNegativeFloat
    memory_usage: NonNegativeFloat
    run_time: NonNegativeFloat
    ngpus: NonNegativeInt
    node: str
    cpu_type: str
    gpu_type: str | None = None
    mem_type: str


class FileSchedulerConfig(BaseModel):
    """File-based scheduler configuration.

    Attributes:
        node_data_file_path (Path): Path to the file containing node data.
    """

    node_data_file_path: Path


class ClusterConfig(BaseModel):  # type: ignore[explicit-any]
    """Configuration for an HPC cluster and hosting data center.

    Attributes:
        cluster_name (str): Name of the HPC cluster.
        region_id (int): Region ID for carbon intensity API (1-17).
        pue (float): Power Usage Effectiveness of the data center.
        cpus (dict): Dictionary of CPU types and their power usage.
        gpus (dict): Dictionary of GPU types and their power usage.
        memory (dict): Dictionary with memory types and their power usage.
        scheduler (str): Scheduler type used by the cluster.
        scheduler_config (dict): Scheduler-specific configuration parameters.
        average_intensity (float | None): Optional average carbon intensity
            in gCO2eq/kWh for the region.
    """

    cluster_name: str
    region_id: int = Field(ge=1, le=17)
    pue: PositiveFloat
    cpus: dict[str, dict[str, float]]
    gpus: dict[str, dict[str, float]]
    memory: dict[str, dict[str, float]]
    scheduler: str
    scheduler_config: dict[str, Any]  # type: ignore[explicit-any]
    average_intensity: NonNegativeFloat | None = None
    min_runtime: NonNegativeFloat = 600
