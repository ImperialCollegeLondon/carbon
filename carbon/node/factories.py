"""Base class for compute nodes."""

import subprocess
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, Self

from ..clusterconfig import DummySchedulerConfig
from .node import Node

ComponentPower = dict[str, dict[str, dict[str, float]]]


class NodeFactory(Protocol):
    """Abstract base class for Node factories."""

    @classmethod
    @abstractmethod
    def from_config(  # type: ignore[explicit-any]
        cls,
        config: dict[str, Any],
        component_powers: ComponentPower,
    ) -> Self:
        """Initialize the NodeFactoryBase with a config.

        Args:
            config (dict): Configuration dictionary.
            component_powers (dict): Dictionary of power usages for components.
        """

    @abstractmethod
    def create(self, node_labels: list[str]) -> list[Node]:
        """Abstract method to create multiple Node objects."""


@dataclass
class DummyNodeFactory(NodeFactory):
    """Dummy factory for creating Node objects with hardcoded values."""

    cpu_type: str
    gpu_type: str | None
    mem_type: str
    node: str
    component_powers: ComponentPower

    @classmethod
    def from_config(  # type: ignore[explicit-any]
        cls,
        config: dict[str, Any],
        component_powers: ComponentPower,
    ) -> Self:
        """Initialize the DummyNodeFactory with a config.

        Args:
            config (dict): Configuration dictionary (not used in dummy factory).
            component_powers (dict): Dictionary of power usages for components.
        """
        validated_config = DummySchedulerConfig(**config)
        return cls(
            cpu_type=validated_config.cpu_type,
            gpu_type=validated_config.gpu_type,
            mem_type=validated_config.mem_type,
            node=validated_config.node,
            component_powers=component_powers,
        )

    def create(self, node_labels: list[str]) -> list[Node]:
        """Create a dummy Node object.

        Args:
            node_labels (list[str]): The label of the node to create.

        Returns:
            Node: An instance of Node with dummy hardware and power info.
        """
        cpu_type = self.cpu_type
        per_core_power_watts = self.component_powers["cpus"][cpu_type][
            "per_core_power_watts"
        ]
        gpu_type = self.gpu_type
        if gpu_type:
            per_gpu_power_watts = self.component_powers["gpus"][gpu_type][
                "per_gpu_power_watts"
            ]
        else:
            per_gpu_power_watts = 0.0

        mem_type = self.mem_type
        per_gb_power_watts = self.component_powers["memory"][mem_type][
            "per_gb_power_watts"
        ]

        return [
            Node(
                name=node,
                cpu_type=cpu_type,
                gpu_type=gpu_type,
                mem_type=mem_type,
                per_core_power_watts=per_core_power_watts,
                per_gpu_power_watts=per_gpu_power_watts,
                per_gb_power_watts=per_gb_power_watts,
            )
            for node in node_labels
        ]


@dataclass
class PBSNodeFactory(NodeFactory):
    """Factory for creating Node objects by querying PBS."""

    component_powers: ComponentPower

    @classmethod
    def from_config(  # type: ignore[explicit-any]
        cls,
        config: dict[str, Any],
        component_powers: ComponentPower,
    ) -> Self:
        """Initialize the DummyNodeFactory with a config.

        Args:
            config (dict): Configuration dictionary (not used in dummy factory).
            component_powers (dict): Dictionary of power usages for components.
        """
        # no use for the config here currently but this could be used to pass in site
        # specific configuration in the future
        return cls(component_powers=component_powers)

    def create(self, node_labels: list[str]) -> list[Node]:
        """Create a Node object by fetching info from PBS and cluster config.

        Args:
            node_labels (list[str]): The labels of the nodes to query.

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
            node_label: str = ""
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
                per_core_power_watts = self.component_powers["cpus"][cpu_type][
                    "per_core_power_watts"
                ]
            except KeyError:
                raise ValueError(f"CPU type '{cpu_type}' not found in cluster config.")

            if gpu_type:
                try:
                    per_gpu_power_watts = self.component_powers["gpus"][gpu_type][
                        "per_gpu_power_watts"
                    ]
                except KeyError:
                    raise ValueError(
                        f"GPU type '{gpu_type}' not found in cluster config."
                    )
            else:
                per_gpu_power_watts = 0.0

            try:
                per_gb_power_watts = self.component_powers["memory"][mem_type][
                    "per_gb_power_watts"
                ]
            except KeyError:
                raise ValueError(
                    f"Memory type '{mem_type}' not found in cluster config."
                )

            if cpu_type is None or cpu_type == "":
                raise ValueError(f"Could not determine cpu_type for node {node_label}")

            node_list.append(
                Node(
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
