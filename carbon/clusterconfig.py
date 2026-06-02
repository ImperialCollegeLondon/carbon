"""Configuration schema for an HPC cluster and its power usage characteristics."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt, PositiveFloat


class DummySchedulerConfig(BaseModel):
    """Optional dummy job specification for testing and development purposes.

    Attributes:
        start_time: Start time of the job in ISO format.
        cpu_time: CPU time used by the job in cpu core-hours.
        memory_usage: Memory allocated to the job in GB.
        run_time: Total run time of the job in hours.
        ngpus: Number of GPUs used by the job.
        node: Label of the node the job was executed on.
        cpu_type: CPU type for dummy job.
        gpu_type: GPU type for dummy job, or None if not present.
        mem_type: Memory type for dummy job
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
        node_data_file_path: Path to the file containing node data.
    """

    node_data_file_path: Path


class CSVExporterConfig(BaseModel):
    """Configuration for exporting results to CSV files.

    Attributes:
        output_path: Path where CSV output will be saved.
    """

    output_path: Path = Path("carbon_output.csv")


class ClusterConfig(BaseModel):
    """Configuration for an HPC cluster and hosting data center.

    Attributes:
        cluster_name: Name of the HPC cluster.
        region_id: Region ID for carbon intensity API (1-17).
        pue: Power Usage Effectiveness of the data center.
        cpus: Dictionary of CPU types and their power usage.
        gpus: Dictionary of GPU types and their power usage.
        memory: Dictionary with memory types and their power usage.
        scheduler: Scheduler type used by the cluster.
        scheduler_config: Scheduler-specific configuration parameters.
        average_intensity: Optional average carbon intensity
            in gCO2eq/kWh for the region.
        exporters: List of exporter types to use for output.
        exporter_config: Dictionary of exporter-specific configuration parameters.
    """

    cluster_name: str
    region_id: int = Field(ge=1, le=17)
    pue: PositiveFloat
    cpus: dict[str, dict[str, float]]
    gpus: dict[str, dict[str, float]]
    memory: dict[str, dict[str, float]]
    scheduler: str
    scheduler_config: dict[str, object]
    average_intensity: NonNegativeFloat | None = None
    exporters: list[str] = []
    exporter_config: dict[str, dict[str, object]] = Field(default_factory=dict)
