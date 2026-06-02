"""Defines the Job dataclass representing a compute job and its resource usage."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..node import Node


class JobState(Enum):
    """Enumeration of supported job states."""

    FINISHED = "F"
    RUNNING = "R"
    EXPIRED = "X"


@dataclass
class EnergyBreakdown:
    """Breakdown of energy consumption by component."""

    cpu: float
    gpu: float
    memory: float
    total: float


@dataclass
class Job:
    """Represents a compute job, including its resource usage and timing information."""

    id: str
    """The job identifier."""

    starttime: datetime
    """The start time of the job."""

    runtime: float
    """The total runtime of the job in hours."""

    cputime: float
    """The total CPU time used by the job in core-hours."""

    gputime: float
    """The total GPU time used by the job in component-hours."""

    memtime: float
    """The total memory-time allocated to the job in GB-hours."""

    node: str
    """The node the job was executed on."""

    state: JobState = JobState.FINISHED
    """The state of the job."""

    def calculate_energy(self, node: Node, pue: float) -> EnergyBreakdown:
        """Calculate energy consumption in kilowatt-hours for a compute job.

        Args:
            node: The compute node the job was executed on.
            pue: Power Usage Effectiveness of the data center.

        Returns:
            The energy consumed broken down by component.
        """
        cpu = node.per_core_power_watts * self.cputime * pue / 1000.0
        gpu = node.per_gpu_power_watts * self.gputime * pue / 1000.0
        memory = node.per_gb_power_watts * self.memtime * pue / 1000.0
        return EnergyBreakdown(
            cpu=cpu, gpu=gpu, memory=memory, total=cpu + gpu + memory
        )
