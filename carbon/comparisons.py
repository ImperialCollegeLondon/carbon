"""Module for comparing compute job emissions to other sources."""

import csv
from abc import ABC, abstractmethod
from pathlib import Path


class EmissionsComparison(ABC):
    """Loads emissions data from csv and compares to job emissions."""

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

    @abstractmethod
    def get_equivalents(self, emissions_gco2: float) -> list[tuple[str, float, str]]:
        """For each item, calculate the amount that would emit the same gCO2."""
        pass

    @abstractmethod
    def print_comparisons(self, emissions_gco2: float) -> None:
        """Prints the equivalent of each item for the given emissions."""
        pass


class Travel(EmissionsComparison):
    """Compares emissions to travel methods."""

    def get_equivalents(self, emissions_gco2: float) -> list[tuple[str, float, str]]:
        """For each item, calculate the amount that would emit the same gCO2."""
        results = []
        for comp in self.comparisons:
            try:
                kilometers = emissions_gco2 / float(comp["gCO2ePerKm"])
                results.append((comp["Method"], kilometers, comp["Note"]))
            except (KeyError, ValueError):
                continue
        return results

    def print_comparisons(self, emissions_gco2: float) -> None:
        """Prints the equivalent of each item for the given emissions."""
        equivalents = self.get_equivalents(emissions_gco2)
        print("Equivalent to:")
        for method, kilometers, note in equivalents:
            print(f"    {method} {kilometers:.1f} km {note}")


class Food(EmissionsComparison):
    """Compares emissions to food data."""

    def get_equivalents(self, emissions_gco2: float) -> list[tuple[str, float, str]]:
        """For each item, calculate the amount that would emit the same gCO2."""
        results = []
        for comp in self.comparisons:
            try:
                kilos = emissions_gco2 / float(comp["gCO2ePerKilo"])
                portions = kilos * float(comp["PortionPerKilo"])
                results.append((comp["Food"], portions, comp["PluralPortionName"]))
            except (KeyError, ValueError):
                continue
        return results

    def print_comparisons(self, emissions_gco2: float) -> None:
        """Prints the equivalent of each item for the given emissions."""
        equivalents = self.get_equivalents(emissions_gco2)
        print("Equivalent to:")
        for food, portions, portion_name in equivalents:
            if portion_name:
                print(f"    {portions:.1f} {portion_name} of {food}")
            else:
                print(f"    {portions:.1f} {food}")
