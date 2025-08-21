"""Unit tests for the Energy class."""

from carbon.energy import Energy


def test_energy_calculate() -> None:
    """Test energy calculation with GPU."""
    energy = Energy(cpupower=10.0, gpupower=200.0, mempower=2.0, pue=1.5)
    # 2 CPU hours, 1 GPU for 2 hours, 16GB for 2 hours, PUE=1.5
    result = energy.calculate(cpuhours=2.0, runtime=2.0, mem=16.0, ngpus=1)
    expected = ((10.0 * 2.0) + (200.0 * 1 * 2.0) + (2.0 * 16.0 * 2.0)) * 1.5 / 1000.0
    assert abs(result - expected) < 1e-6


def test_energy_no_gpu() -> None:
    """Test energy calculation without GPU."""
    energy = Energy(cpupower=10.0, gpupower=0.0, mempower=2.0, pue=1.2)
    result = energy.calculate(cpuhours=1.0, runtime=1.0, mem=8.0, ngpus=0)
    expected = ((10.0 * 1.0) + (0.0 * 0 * 1.0) + (2.0 * 8.0 * 1.0)) * 1.2 / 1000.0
    assert abs(result - expected) < 1e-6
