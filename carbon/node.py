"""The node submodule.

This module holds functionality for representing a compute node, including fetching
information about the hardware components.
"""

import subprocess
from typing import Self


class Node:
    """Represents a compute node, including hardware models and power usage.

    Attributes:
        name (str): The node label.
        cpu_type (str): The CPU model.
        gpu_type (str | None): The GPU model, or None if GPU not present.
        mem_type (str): The memory type.
        per_core_power_watts (float): Power usage per CPU core in watts.
        per_gpu_power_watts (float | None): Power usage per GPU in watts. Zero if GPU
            not present.
        per_gb_power_watts (float): Power usage per GB of memory in watts.
    """

    def __init__(
        self,
        name: str,
        cpu_type: str,
        gpu_type: str | None,
        mem_type: str,
        per_core_power_watts: float,
        per_gpu_power_watts: float,
        per_gb_power_watts: float,
    ) -> None:
        """Initialize the Node object.

        Args:
            name (str): The node label.
            cpu_type (str): The CPU model.
            gpu_type (str | None): The GPU model, or None if GPU not present.
            mem_type (str): The memory type.
            per_core_power_watts (float): Power usage per CPU core in watts.
            per_gpu_power_watts (float): Power usage per GPU in watts. Zero if
                GPU not present.
            per_gb_power_watts (float): Power usage per GB of memory in watts.
        """
        self.name = name
        self.cpu_type = cpu_type
        self.gpu_type = gpu_type
        self.mem_type = mem_type
        self.per_core_power_watts = per_core_power_watts
        self.per_gpu_power_watts = per_gpu_power_watts
        self.per_gb_power_watts = per_gb_power_watts

    @classmethod
    def fromPBS(
        cls, node_label: str, component_powers: dict[str, dict[str, dict[str, float]]]
    ) -> Self:
        """Create a Node object by fetching info from PBS and cluster config.

        Args:
            node_label (str): The label of the node to query.
            component_powers (dict): Dictionary with keys 'cpus', 'gpus', 'memory'.

        Returns:
            Node: An instance of Node with hardware and power info.
        """
        cmd = f'qmgr -c "list node {node_label}"'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        cpu_type: str = ""
        gpu_type: str | None = None
        mem_type: str = "common"  # Memory hardcoded to common type
        for line in result.stdout.splitlines():
            if "resources_available.cpu_type" in line:
                cpu_type = line.split("=")[-1].strip()
            if "resources_available.gpu_type" in line:
                val = line.split("=")[-1].strip()
                gpu_type = val if val != "None" else None

        # Look up power usage for cpu/gpu/memory
        try:
            per_core_power_watts = component_powers["cpus"][cpu_type][
                "per_core_power_watts"
            ]
        except KeyError:
            raise ValueError(f"CPU type '{cpu_type}' not found in cluster config.")

        if gpu_type:
            try:
                per_gpu_power_watts = component_powers["gpus"][gpu_type][
                    "per_gpu_power_watts"
                ]
            except KeyError:
                raise ValueError(f"GPU type '{gpu_type}' not found in cluster config.")
        else:
            per_gpu_power_watts = 0.0

        try:
            per_gb_power_watts = component_powers["memory"][mem_type][
                "per_gb_power_watts"
            ]
        except KeyError:
            raise ValueError(f"Memory type '{mem_type}' not found in cluster config.")

        if cpu_type is None or cpu_type == "":
            raise ValueError(f"Could not determine cpu_type for node {node_label}")

        return cls(
            name=node_label,
            cpu_type=cpu_type,
            gpu_type=gpu_type,
            mem_type=mem_type,
            per_core_power_watts=per_core_power_watts,
            per_gpu_power_watts=per_gpu_power_watts,
            per_gb_power_watts=per_gb_power_watts,
        )
