"""Module for comparing compute job emissions to other sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel, PositiveFloat

ComparisonRow = tuple[str, float, str]


class EmissionsComparison(ABC):
    """Abstract base class for comparing compute job emissions to other sources."""

    @abstractmethod
    def get_equivalents(self, emissions_gco2: float) -> list[ComparisonRow]:
        """Calculates the amount of each item that would emit the same emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 to compare against.

        Returns:
            list[ComparisonRow]: List of (item, amount, unit/note) tuples.
        """
        pass

    @abstractmethod
    def format_line(self, item: str, amount: float, unit: str) -> str:
        """Format a single comparison line.

        Args:
            item (str): The name of the item.
            amount (float): The amount of the item.
            unit (str): The unit or note for the amount.

        Returns:
            str: Formatted comparison line.
        """
        pass

    def output_text(self, emissions_gco2: float) -> str:
        """Print the equivalent travel distances for the given emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 to compare against.
        """
        output = "Equivalent to:\n"
        output += "\n".join(
            self.format_line(*equivalent)
            for equivalent in self.get_equivalents(emissions_gco2)
        )
        return output


class TravelComparisonData(BaseModel):
    """Data model for travel comparison data."""

    method: str
    gCO2e_per_km: PositiveFloat
    note: str


@dataclass
class Travel(EmissionsComparison):
    """Compares emissions to travel methods using reference data."""

    comparisons: list[TravelComparisonData]

    def get_equivalents(self, emissions_gco2: float) -> list[ComparisonRow]:
        """Calculates the distance via each method that would emit the same emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 to compare against.

        Returns:
            list[tuple[str, float, str]]: List of (method, kilometers, note) tuples.
        """
        return [
            (comp.method, emissions_gco2 / comp.gCO2e_per_km, comp.note)
            for comp in self.comparisons
        ]

    def format_line(self, item: str, amount: float, unit: str) -> str:
        """Format a single comparison line.

        Args:
            item (str): The name of the item.
            amount (float): The amount of the item.
            unit (str): The unit or note for the amount.

        Returns:
            str: Formatted comparison line.
        """
        return f"    {item} {amount:.1f} km {unit}"


class FoodComparisonData(BaseModel):
    """Data model for food comparison data."""

    food: str
    gCO2e_per_kilo: PositiveFloat
    portion_per_kilo: PositiveFloat
    plural_portion_name: str


@dataclass
class Food(EmissionsComparison):
    """Compares emissions to food data using reference data."""

    comparisons: list[FoodComparisonData]

    def get_equivalents(self, emissions_gco2: float) -> list[ComparisonRow]:
        """Calculate the number of portions that would emit the same emissions.

        Args:
            emissions_gco2 (float): The emissions in grams of CO2 to compare against.

        Returns:
            list[tuple[str, float, str]]: List of (food, portions, portion_name) tuples.
        """
        return [
            (
                comp.food,
                emissions_gco2 / comp.gCO2e_per_kilo * comp.portion_per_kilo,
                comp.plural_portion_name,
            )
            for comp in self.comparisons
        ]

    def format_line(self, item: str, amount: float, unit: str) -> str:
        """Format a single comparison line.

        Args:
            item (str): The name of the item.
            amount (float): The amount of the item.
            unit (str): The unit or note for the amount.

        Returns:
            str: Formatted comparison line.
        """
        if unit:
            return f"    {amount:.1f} {unit} of {item}"
        else:
            return f"    {amount:.1f} {item}"
