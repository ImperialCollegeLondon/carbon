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

    def calculate_energy(self, node: Node, pue: float) -> float:
        """Calculate energy consumption in kilowatt-hours for a compute job.

        Args:
            node (Node): The compute node the job was executed on.
            pue (float): Power Usage Effectiveness of the data center.

        Returns:
            float: The energy consumed in kilowatt-hours.
        """
        return (
            (
                node.per_core_power_watts * self.cputime
                + node.per_gpu_power_watts * self.gputime
                + node.per_gb_power_watts * self.memtime
            )
            * pue
            / 1000.0
        )
