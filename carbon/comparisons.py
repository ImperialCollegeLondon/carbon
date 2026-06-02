"""Module for comparing compute job emissions to other sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel, PositiveFloat


@dataclass
class ComparisonRow:
    """Represents a single comparison row for emissions comparisons."""

    item: str
    amount: float
    unit: str


class EmissionsComparison(ABC):
    """Abstract base class for comparing compute job emissions to other sources."""

    @abstractmethod
    def get_equivalents(self, emissions_gco2: float) -> list[ComparisonRow]:
        """Calculates the amount of each item that would emit the same emissions.

        Args:
            emissions_gco2: The emissions in grams of CO2 to compare against.

        Returns:
            List of (item, amount, unit/note) tuples.
        """
        pass


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
            emissions_gco2: The emissions in grams of CO2 to compare against.

        Returns:
            List of (method, kilometers, note) tuples.
        """
        return [
            ComparisonRow(comp.method, emissions_gco2 / comp.gCO2e_per_km, comp.note)
            for comp in self.comparisons
        ]


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
            emissions_gco2: The emissions in grams of CO2 to compare against.

        Returns:
            List of (food, portions, portion_name) tuples.
        """
        return [
            ComparisonRow(
                comp.food,
                emissions_gco2 / comp.gCO2e_per_kilo * comp.portion_per_kilo,
                comp.plural_portion_name,
            )
            for comp in self.comparisons
        ]
