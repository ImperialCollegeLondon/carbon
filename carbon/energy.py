"""The energy module.

This module provides functionality to calculate energy consumption.
"""


class Energy:
    """A class to represent energy consumption."""

    def __init__(
        self, cpupower: float, gpupower: float, mempower: float, pue: float
    ) -> None:
        """Initialize the Energy object.

        Args:
            cpupower: Power usage per CPU core in watts.
            gpupower: Power usage per GPU in watts.
            mempower: Power usage per GB of memory in watts.
            pue: Power Usage Effectiveness of the data center.
        """
        self._cpupower = cpupower
        self._gpupower = gpupower
        self._mempower = mempower
        self._pue = pue

    def calculate(
        self, cpuhours: float, runtime: float, mem: float, ngpus: int
    ) -> float:
        """Calculate energy consumption in kilowatt-hours.

        Args:
            cpuhours: The per-core CPU hours consumed by the job in core-hours.
            runtime: The total runtime of the job in hours.
            mem: The memory allocated to the job in GB.
            ngpus: The number of GPUs used by the job.

        Returns:
            The energy consumed in kilowatt-hours.
        """
        return (
            (
                self._cpupower * cpuhours
                + self._gpupower * ngpus * runtime
                + self._mempower * mem * runtime
            )
            * self._pue
            / 1000.0
        )
