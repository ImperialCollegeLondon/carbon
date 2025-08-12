"""Module for comparing compute job emissions to other sources."""

import csv
from abc import ABC, abstractmethod
from pathlib import Path


class EmissionsComparison(ABC):
    """Abstract base class for comparing compute job emissions to other sources.

    Args:
        data_path (Path): Path to the CSV file containing comparison data.
    """

    def __init__(self, data_path: Path) -> None:
        """Initialize the EmissionsComparison object and load comparison data from CSV.

        Args:
            data_path (Path): Path to the CSV file containing comparison data.
        """
        self.data_path = data_path
        self.comparisons = self._load_comparisons()

    def _load_comparisons(self) -> list[dict[str, str]]:
        """Load comparison data from a CSV file.

        Returns:
            list[dict[str, str]]: List of dictionaries, each representing a row from the
                CSV file.
        """
        comparisons = []
        with open(self.data_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                comparisons.append(row)
        return comparisons

    @abstractmethod
    def get_equivalents(self, emissions_gco2: float) -> list[tuple[str, float, str]]:
        """Calculates the amount of each item that would emit the same emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 equivalent to compare
                against.

        Returns:
            list[tuple[str, float, str]]: List of (item, amount, unit/note) tuples.
        """
        pass

    @abstractmethod
    def print_comparisons(self, emissions_gco2: float) -> None:
        """Print the equivalent of each item for the given emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 equivalent to compare
                against.
        """
        pass


class Travel(EmissionsComparison):
    """Compares emissions to travel methods using reference data."""

    def get_equivalents(self, emissions_gco2: float) -> list[tuple[str, float, str]]:
        """Calculates the distance via each method that would emit the same emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 equivalent to compare
                against.

        Returns:
            list[tuple[str, float, str]]: List of (method, kilometers, note) tuples.
        """
        results = []
        for comp in self.comparisons:
            try:
                kilometers = emissions_gco2 / float(comp["gCO2ePerKm"])
                results.append((comp["Method"], kilometers, comp["Note"]))
            except (KeyError, ValueError):
                continue
        return results

    def print_comparisons(self, emissions_gco2: float) -> None:
        """Print the equivalent travel distances for the given emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 equivalent to compare
                against.
        """
        equivalents = self.get_equivalents(emissions_gco2)
        print("Equivalent to:")
        for method, kilometers, note in equivalents:
            print(f"    {method} {kilometers:.1f} km {note}")


class Food(EmissionsComparison):
    """Compares emissions to food data using reference data."""

    def get_equivalents(self, emissions_gco2: float) -> list[tuple[str, float, str]]:
        """Calculate the number of portions that would emit the same emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 equivalent to compare
                against.

        Returns:
            list[tuple[str, float, str]]: List of (food, portions, portion_name) tuples.
        """
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
        """Print the equivalent food portions for the given emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 equivalent to compare
                against.
        """
        equivalents = self.get_equivalents(emissions_gco2)
        print("Equivalent to:")
        for food, portions, portion_name in equivalents:
            if portion_name:
                print(f"    {portions:.1f} {portion_name} of {food}")
            else:
                print(f"    {portions:.1f} {food}")
