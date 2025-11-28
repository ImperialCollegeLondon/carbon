"""Defines the Node dataclass representing a compute node."""

from dataclasses import dataclass


@dataclass
class Node:
    """Represents a compute node, including hardware models and power usage."""

    name: str
    """The node label."""

    cpu_type: str
    """The CPU model."""

    gpu_type: str | None
    """The GPU model, or None if GPU not present."""

    mem_type: str
    """The memory type."""

    per_core_power_watts: float
    """Power usage per CPU core in watts."""

    per_gpu_power_watts: float
    """Power usage per GPU in watts. Zero if GPU not present."""

    per_gb_power_watts: float
    """Power usage per GB of memory in watts."""
