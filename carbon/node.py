"""The node submodule.

This module holds functionality for representing a compute node, including fetching
information about the hardware components.
"""

import subprocess
from dataclasses import dataclass
from typing import Self


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

    @classmethod
    def from_PBS(
        cls,
        node_labels: list[str],
        component_powers: dict[str, dict[str, dict[str, float]]],
    ) -> list[Self]:
        """Create a Node object by fetching info from PBS and cluster config.

        Args:
            node_labels (list[str]): The labels of the nodes to query.
            component_powers (dict): Dictionary with keys 'cpus', 'gpus', 'memory'.

        Returns:
            list[Node]: A list of Node instances with hardware and power info.
        """
        # list of object ids passed to qmgr should be comma-seperated
        cmd = 'qmgr -c "list node ' + ",".join(node_labels) + '"'
        result = subprocess.run(
            cmd, shell=True, timeout=20, capture_output=True, text=True, check=True
        )

        node_list = []

        node_info_list = [lines for lines in result.stdout.split("\n\n") if lines]
        for node_info in node_info_list:
            node_label: str
            cpu_type: str = ""
            gpu_type: str | None = None
            mem_type: str = "common"  # Memory hardcoded to common type
            for line in node_info.splitlines():
                if line.lstrip().startswith("resources_available"):
                    if line.lstrip().startswith("resources_available.host"):
                        node_label = line.split("=")[-1].strip()
                    if line.lstrip().startswith("resources_available.cpu_type"):
                        cpu_type = line.split("=")[-1].strip()
                    if line.lstrip().startswith("resources_available.gpu_type"):
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
                    raise ValueError(
                        f"GPU type '{gpu_type}' not found in cluster config."
                    )
            else:
                per_gpu_power_watts = 0.0

            try:
                per_gb_power_watts = component_powers["memory"][mem_type][
                    "per_gb_power_watts"
                ]
            except KeyError:
                raise ValueError(
                    f"Memory type '{mem_type}' not found in cluster config."
                )

            if cpu_type is None or cpu_type == "":
                raise ValueError(f"Could not determine cpu_type for node {node_label}")

            node_list.append(
                cls(
                    name=node_label,
                    cpu_type=cpu_type,
                    gpu_type=gpu_type,
                    mem_type=mem_type,
                    per_core_power_watts=per_core_power_watts,
                    per_gpu_power_watts=per_gpu_power_watts,
                    per_gb_power_watts=per_gb_power_watts,
                )
            )
        return node_list
