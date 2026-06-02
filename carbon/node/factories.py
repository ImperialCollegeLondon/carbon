"""Base class for compute nodes."""

import subprocess
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Self

import pydantic
import yaml

from ..clusterconfig import DummySchedulerConfig, FileSchedulerConfig
from .node import Node

ComponentPower = dict[str, dict[str, dict[str, float]]]


class NodeFactory(Protocol):
    """Abstract base class for Node factories."""

    @classmethod
    @abstractmethod
    def from_config(
        cls, config: dict[str, object], component_powers: ComponentPower
    ) -> Self:
        """Initialize the NodeFactoryBase with a config.

        Args:
            config: Configuration dictionary.
            component_powers: Dictionary of power usages for components.
        """

    @abstractmethod
    def create(self, node_labels: list[str]) -> list[Node]:
        """Abstract method to create multiple Node objects."""

    def _make_node(
        self,
        name: str,
        cpu_type: str,
        gpu_type: str | None,
        mem_type: str,
        component_powers: ComponentPower,
    ) -> Node:
        """Create a Node object given hardware types.

        Args:
            name: The node label.
            cpu_type: The CPU model.
            gpu_type: The GPU model, or None if not present.
            mem_type: The memory type.
            component_powers: Dictionary of power usages for components.

        Returns:
            An instance of Node with hardware and power info.
        """
        try:
            per_core_power_watts = component_powers["cpus"][cpu_type][
                "per_core_power_watts"
            ]
        except KeyError:
            raise ValueError(f"CPU type '{cpu_type}' not found in cluster config.")

        if gpu_type is None:
            per_gpu_power_watts = 0.0
        else:
            try:
                per_gpu_power_watts = component_powers["gpus"][gpu_type][
                    "per_gpu_power_watts"
                ]
            except KeyError:
                raise ValueError(f"GPU type '{gpu_type}' not found in cluster config.")

        try:
            per_gb_power_watts = component_powers["memory"][mem_type][
                "per_gb_power_watts"
            ]
        except KeyError:
            raise ValueError(f"Memory type '{mem_type}' not found in cluster config.")

        return Node(
            name=name,
            cpu_type=cpu_type,
            gpu_type=gpu_type,
            mem_type=mem_type,
            per_core_power_watts=per_core_power_watts,
            per_gpu_power_watts=per_gpu_power_watts,
            per_gb_power_watts=per_gb_power_watts,
        )


@dataclass
class DummyNodeFactory(NodeFactory):
    """Dummy factory for creating Node objects with hardcoded values."""

    cpu_type: str
    gpu_type: str | None
    mem_type: str
    node: str
    component_powers: ComponentPower

    @classmethod
    def from_config(
        cls, config: dict[str, object], component_powers: ComponentPower
    ) -> Self:
        """Initialize the DummyNodeFactory with a config.

        Args:
            config: Configuration dictionary (not used in dummy factory).
            component_powers: Dictionary of power usages for components.
        """
        validated_config = DummySchedulerConfig.model_validate(config)
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
            node_labels: The label of the node to create.

        Returns:
            An instance of Node with dummy hardware and power info.
        """
        return [
            self._make_node(
                name=node,
                cpu_type=self.cpu_type,
                gpu_type=self.gpu_type,
                mem_type=self.mem_type,
                component_powers=self.component_powers,
            )
            for node in node_labels
        ]


@dataclass
class PBSNodeFactory(NodeFactory):
    """Factory for creating Node objects by querying PBS."""

    component_powers: ComponentPower

    @classmethod
    def from_config(
        cls, config: dict[str, object], component_powers: ComponentPower
    ) -> Self:
        """Initialize the DummyNodeFactory with a config.

        Args:
            config: Configuration dictionary (not used in dummy factory).
            component_powers: Dictionary of power usages for components.
        """
        # no use for the config here currently but this could be used to pass in site
        # specific configuration in the future
        return cls(component_powers=component_powers)

    def create(self, node_labels: list[str]) -> list[Node]:
        """Create a Node object by fetching info from PBS and cluster config.

        Args:
            node_labels: The labels of the nodes to query.

        Returns:
            A list of Node instances with hardware and power info.
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

            if cpu_type is None or cpu_type == "":
                raise ValueError(f"Could not determine cpu_type for node {node_label}")

            node_list.append(
                self._make_node(
                    name=node_label,
                    cpu_type=cpu_type,
                    gpu_type=gpu_type,
                    mem_type=mem_type,
                    component_powers=self.component_powers,
                )
            )
        return node_list


@dataclass
class FileNodeFactory(NodeFactory):
    """Factory for creating Node objects from data in a file."""

    component_powers: ComponentPower
    node_data_file_path: Path

    @classmethod
    def from_config(
        cls, config: dict[str, object], component_powers: ComponentPower
    ) -> Self:
        """Initialize the FileNodeFactory with a config.

        Args:
            config: Configuration dictionary.
            component_powers: Dictionary of power usages for components.
        """
        validated_config = FileSchedulerConfig.model_validate(config)

        return cls(
            component_powers=component_powers,
            node_data_file_path=validated_config.node_data_file_path,
        )

    class NodeDataModel(pydantic.BaseModel):
        """Pydantic model for node data in file."""

        cpu_type: str
        gpu_type: str | None = None
        mem_type: str

    def create(self, node_labels: list[str]) -> list[Node]:
        """Create a Node object by fetching info from a file.

        Args:
            node_labels: The labels of the nodes to query.

        Returns:
            A list of Node instances with hardware and power info.
        """
        if len(node_labels) != 1:
            raise ValueError(
                "FileNodeFactory can only create one node at a time from file."
            )

        with self.node_data_file_path.open() as f:
            node_data = self.NodeDataModel(**yaml.safe_load(f))
        return [
            self._make_node(
                name=node_label,
                cpu_type=node_data.cpu_type,
                gpu_type=node_data.gpu_type,
                mem_type=node_data.mem_type,
                component_powers=self.component_powers,
            )
            for node_label in node_labels
        ]
