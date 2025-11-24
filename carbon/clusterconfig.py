"""Configuration schema for an HPC cluster and its power usage characteristics."""

from datetime import datetime

from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt, PositiveFloat


class DummyJob(BaseModel):
    """Optional dummy job specification for testing and development purposes.

    Attributes:
        start_time (datetime): Start time of the job in ISO format.
        run_time (float): Total run time of the job in hours.
        cpu_time (float): CPU time used by the job in cpu core-hours.
        ncpus (int): Number of CPU cores used by the job.
        ngpus (int): Number of GPUs used by the job.
        memory (float): Memory allocated to the job in GB.
        node (str): Label of the node the job was executed on.
        cpu_type (str): CPU type for dummy job.
        gpu_type (str | None): GPU type for dummy job, or None if not present.
        mem_type (str): Memory type for dummy job
    """

    start_time: datetime
    run_time: NonNegativeFloat
    cpu_time: NonNegativeFloat
    ncpus: NonNegativeInt
    ngpus: NonNegativeInt
    memory: NonNegativeFloat
    node: str
    cpu_type: str
    gpu_type: str | None = None
    mem_type: str


class ClusterConfig(BaseModel):
    """Configuration for an HPC cluster and hosting data center.

    Attributes:
        cluster_name (str): Name of the HPC cluster.
        region_id (int): Region ID for carbon intensity API (1-17).
        pue (float): Power Usage Effectiveness of the data center.
        cpus (dict): Dictionary of CPU types and their power usage.
        gpus (dict): Dictionary of GPU types and their power usage.
        memory (dict): Dictionary with memory types and their power usage.
        dummy_job (DummyJob | None): Optional dummy job specification.
    """

    cluster_name: str
    region_id: int = Field(ge=1, le=17)
    pue: PositiveFloat
    cpus: dict[str, dict[str, float]]
    gpus: dict[str, dict[str, float]]
    memory: dict[str, dict[str, float]]
    dummy_job: DummyJob | None = None
