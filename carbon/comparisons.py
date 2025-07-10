"""Module for comparing compute job emissions to other sources."""

import csv
from pathlib import Path


class EmissionsComparison:
    """Loads comparison data and provides methods to compare emissions."""

    def __init__(self, data_path: Path) -> None:
        """Initialize the EmissionsComparison object."""
        self.data_path = data_path
        self.comparisons = self._load_comparisons()

    def _load_comparisons(self) -> list[dict[str, str]]:
        """Load comparison data from a CSV file."""
        comparisons = []
        with open(self.data_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                comparisons.append(row)
        return comparisons

    def get_equivalents(self, emissions_gco2: float) -> list[tuple[str, float, str]]:
        """For each item, calculate the amount that would emit the same gCO2."""
        results = []
        for comp in self.comparisons:
            try:
                value = float(comp["Value"])
                scale_unit = comp["Unit"].lstrip("gCO2e/")
                amount = emissions_gco2 / value
                results.append((comp["Name"], amount, scale_unit))
            except (KeyError, ValueError):
                continue
        return results

    def print_comparisons(self, emissions_gco2: float) -> None:
        """Prints the equivalent of each item for the given emissions."""
        equivalents = self.get_equivalents(emissions_gco2)
        for activity, amount, unit in equivalents:
            print(f"Equivalent to {amount:.1f} {unit} of {activity}")
