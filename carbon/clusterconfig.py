"""Configuration schema for an HPC cluster and its power usage characteristics."""

from datetime import datetime

from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt, PositiveFloat


class DummyJob(BaseModel):
    """Optional dummy job specification for testing and development purposes.

    Attributes:
        start_time (datetime): Start time of the job in ISO format.
        cpu_time (float): CPU time used by the job in cpu core-hours.
        memory_usage (float): Memory allocated to the job in GB.
        run_time (float): Total run time of the job in hours.
        ngpus (int): Number of GPUs used by the job.
        node (str): Label of the node the job was executed on.
    """

    start_time: datetime
    """Start time of the job in ISO format."""
    cpu_time: NonNegativeFloat
    """CPU time used by the job in cpu core-hours."""
    memory_usage: NonNegativeFloat
    """Memory allocated to the job in GB."""
    run_time: NonNegativeFloat
    """Total run time of the job in hours."""
    ngpus: NonNegativeInt
    """Number of GPUs used by the job."""
    node: str
    """Label of the node the job was executed on."""


class Partition(BaseModel):
    """Hardware specification for a partition of the cluster type.

    Attributes:
        name (str): Name of the type of node.
        cpu_model (str): The model of CPU.
        per_core_power_watts (float): Power usage per CPU core in watt.
        gpu_model (str): The model of GPU.
        per_gpu_power_watts (float): Power usage per GPU in watts.
        per_gb_power_watts (float): Power usage per GB of memory in watts.
        node_prefixes (List[str]): List of partial node labels, for nodes belonging
            to this partition of the cluster.
    """

    name: str
    """Name of the type of node."""
    cpu_model: str
    """The model of CPU."""
    per_core_power_watts: NonNegativeFloat
    """Power usage per CPU core in watt."""
    gpu_model: str | None = None
    """The model of GPU."""
    per_gpu_power_watts: NonNegativeFloat | None = None
    """Power usage per GPU in watts."""
    per_gb_power_watts: NonNegativeFloat
    """Power usage per GB of memory in watts."""
    node_prefixes: list[str]
    """List of partial names of nodes belonging to this partition."""


class ClusterConfig(BaseModel):
    """Configuration for an HPC cluster and hosting data center.

    Attributes:
        cluster_name (str): Name of the HPC cluster.
        pue (float): Power Usage Effectiveness of the data center.
        partitions (List[Partition]): List of partitions of the cluster,
            each containing a single node types.
        dummy_job (DummyJob | None): Optional dummy job specification.
    """

    cluster_name: str
    """Name of the HPC cluster."""
    pue: PositiveFloat
    """Power Usage Effectiveness of the data center."""
    partitions: list[Partition]
    """List of partitions of the cluster, each containing a single node types."""
    dummy_job: DummyJob | None = None
    """Optional dummy job specification."""
