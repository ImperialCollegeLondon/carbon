"""The energy module.

This module provides functionality to calculate energy consumption.
"""


class Energy:
    """Represents energy consumption calculations for a compute job.

    Attributes:
        _cpupower (float): Power usage per CPU core in watts.
        _gpupower (float): Power usage per GPU in watts.
        _mempower (float): Power usage per GB of memory in watts.
        _pue (float): Power Usage Effectiveness of the data center.
    """

    def __init__(
        self, cpupower: float, gpupower: float, mempower: float, pue: float
    ) -> None:
        """Initialize the Energy object.

        Args:
            cpupower (float): Power usage per CPU core in watts.
            gpupower (float): Power usage per GPU in watts.
            mempower (float): Power usage per GB of memory in watts.
            pue (float): Power Usage Effectiveness of the data center.
        """
        self._cpupower = cpupower
        self._gpupower = gpupower
        self._mempower = mempower
        self._pue = pue

    def calculate(
        self, cpuhours: float, runtime: float, mem: float, ngpus: int
    ) -> float:
        """Calculate energy consumption in kilowatt-hours for a compute job.

        Args:
            cpuhours (float): The per-core CPU hours consumed by the job in core-hours.
            runtime (float): The total runtime of the job in hours.
            mem (float): The memory allocated to the job in GB.
            ngpus (int): The number of GPUs used by the job.

        Returns:
            float: The energy consumed in kilowatt-hours.
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
