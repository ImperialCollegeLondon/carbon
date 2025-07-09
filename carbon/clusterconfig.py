"""Configuration schema for an HPC cluster and its power usage characteristics."""

from datetime import datetime

from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt, PositiveFloat


class CPUConfig(BaseModel):
    """Configuration for CPU power usage."""

    per_core_power_watts: NonNegativeFloat
    """Power usage per CPU core in watt"""


class GPUConfig(BaseModel):
    """Configuration for GPU power usage."""

    per_gpu_power_watts: NonNegativeFloat
    """Power usage per GPU in watts"""


class MemoryConfig(BaseModel):
    """Configuration for memory power usage."""

    per_gb_power_watts: NonNegativeFloat
    """Power usage per GB of memory in watts"""


class DummyJob(BaseModel):
    """Optional dummy job specification for testing and development purposes."""

    start_time: datetime
    """Start time of the job in ISO format"""

    cpu_time: NonNegativeFloat
    """CPU time used by the job in cpu core-hours"""

    memory_usage: NonNegativeFloat
    """Memory allocated to the job in GB"""

    run_time: NonNegativeFloat
    """Total run time of the job in hours"""

    ngpus: NonNegativeInt
    """Number of GPUs used by the job"""


class ClusterConfig(BaseModel):
    """Configuration for an HPC cluster and hosting data center."""

    cluster_name: str
    """Name of the HPC cluster"""

    pue: PositiveFloat
    """Power Usage Effectiveness of the data center"""

    cpus: CPUConfig
    """CPU configuration"""

    gpus: GPUConfig
    """GPU configuration"""

    memory: MemoryConfig
    """Memory configuration"""

    dummy_job: DummyJob | None = None
    """Optional dummy job specification"""
