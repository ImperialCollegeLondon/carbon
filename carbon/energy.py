"""The energy module.

This module provides functionality to calculate energy consumption.
"""


class Energy:
    """A class to represent energy consumption."""

    CPUPOWER = 12.0  # Watts per core.

    def __init__(self, ncores: int, walltime: float) -> None:
        """Initialize the Energy object.

        Args:
            ncores: The number of CPU cores.
            walltime: The length of time the compute job ran for in hours.
        """
        self._ncores = ncores
        self._walltime = walltime

    def calculate(self) -> float:
        """Calculate energy consumption in watt-hours.

        Returns:
            The energy consumed in kilowatt-hours.
        """
        return (self.CPUPOWER * self._ncores * self._walltime) / 1000.0
