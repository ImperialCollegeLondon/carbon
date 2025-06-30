"""The energy module.

This module provides functionality to calculate energy consumption.
"""


class Energy:
    """A class to represent energy consumption."""

    CPUPOWER = 12.0  # Watts per core.

    def __init__(self, cpuhours: float) -> None:
        """Initialize the Energy object.

        Args:
            cpuhours: The CPU hours consumed by the job.
        """
        self._cpuhours = cpuhours

    def calculate(self) -> float:
        """Calculate energy consumption in kilowatt-hours.

        Returns:
            The energy consumed in kilowatt-hours.
        """
        return (self.CPUPOWER * self._cpuhours) / 1000.0
