"""Unit tests for the Node class."""

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
