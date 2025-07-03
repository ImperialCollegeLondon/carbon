"""The energy module.

This module provides functionality to calculate energy consumption.
"""


class Energy:
    """A class to represent energy consumption."""

    CPUPOWER = 12.0  # Watts per core.
    MEMPOWER = 0.3725  # Watts per GB of allocated RAM. From DOI:10.1002/advs.202100707
    PUE = 1.5  # Power Usage Effectiveness.

    # ToDo: vary CPUPOWER based on CPU type
    # (Can get 'TDP' from manufacturer. Then look up which nodes have which CPU types)
    # ToDo: find out value of PUE data centers used by Imperial. May need to
    # vary based on cluster.

    def __init__(self, cpuhours: float, runtime: float, mem: float) -> None:
        """Initialize the Energy object.

        Args:
            cpuhours: The CPU hours consumed by the job.
            mem: The memory allocated to the job in GB.
            runtime: The total runtime of the job in hours.
        """
        # CHECK: does CPUhours assume 100% CPU usage?
        self._cpuhours = cpuhours
        self._mem = mem
        self._runtime = runtime

    def calculate(self) -> float:
        """Calculate energy consumption in kilowatt-hours.

        Returns:
            The energy consumed in kilowatt-hours.
        """
        return (
            (self.CPUPOWER * self._cpuhours + self.MEMPOWER * self._mem * self._runtime)
            * self.PUE
            / 1000.0
        )
