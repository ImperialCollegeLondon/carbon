"""Unit tests for the Node class."""

from pathlib import Path

import pytest

from carbon.node import Node


def test_node_init() -> None:
    """Test Node initialization with GPU."""
    node = Node(
        name="node01",
        cpu_type="Intel-Xeon",
        gpu_type="NVIDIA-A100",
        mem_type="common",
        per_core_power_watts=12.5,
        per_gpu_power_watts=250.0,
        per_gb_power_watts=3.0,
    )
    assert node.name == "node01"
    assert node.cpu_type == "Intel-Xeon"
    assert node.gpu_type == "NVIDIA-A100"
    assert node.mem_type == "common"
    assert node.per_core_power_watts == 12.5
    assert node.per_gpu_power_watts == 250.0
    assert node.per_gb_power_watts == 3.0


def test_node_init_no_gpu() -> None:
    """Test Node initialization without GPU."""
    node = Node(
        name="node02",
        cpu_type="AMD-EPYC",
        gpu_type=None,
        mem_type="common",
        per_core_power_watts=15.0,
        per_gpu_power_watts=0.0,
        per_gb_power_watts=2.5,
    )
    assert node.gpu_type is None
    assert node.per_gpu_power_watts == 0.0


@pytest.mark.parametrize("gpu_type", ["RTX6000", None])
def test_file_node_factory_create(tmp_path: Path, gpu_type: str | None) -> None:
    """Test FileNodeFactory.create() with a temporary node definition file."""
    import yaml

    from carbon.node.factories import FileNodeFactory

    component_powers = {
        "cpus": {"rome": dict(per_core_power_watts=10.0)},
        "gpus": {"RTX6000": dict(per_gpu_power_watts=200.0)},
        "memory": {"common": dict(per_gb_power_watts=0.5)},
    }
    cpu_type = "rome"
    mem_type = "common"
    node_file_path = tmp_path / "node_info.yaml"
    node_file_path.write_text(
        yaml.dump(
            dict(
                cpu_type=cpu_type,
                gpu_type=gpu_type,
                mem_type=mem_type,
            )
        )
    )

    factory = FileNodeFactory(component_powers, node_file_path)
    node_name = "node01"
    [node] = factory.create([node_name])

    assert node == Node(
        name=node_name,
        cpu_type=cpu_type,
        gpu_type=gpu_type,
        mem_type=mem_type,
        **component_powers["cpus"]["rome"],
        **(
            component_powers["gpus"]["RTX6000"]
            if gpu_type
            else {"per_gpu_power_watts": 0.0}
        ),
        **component_powers["memory"]["common"],
    )
