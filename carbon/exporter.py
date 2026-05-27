"""The carbon exporter module.

This module provides functionality to fetch and display carbon intensity data.
Data is fetched from the Carbon Intensity API (carbonintensity.org.uk) based on the
specified region and time period.
"""

import csv
import os
from abc import abstractmethod
from typing import Protocol, Self

from carbon import RunResult


class Exporter(Protocol):
    """Abstract base class for Exporters."""

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, object]) -> Self:
        """Create an instance of the class from a configuration data."""

    @abstractmethod
    def export(self, run_result: list[RunResult]) -> None:
        """Export the results to a CSV file, one row per job.

        Args:
            run_result (list[RunResult]): The results to export.
        """


class CSVExporter(Exporter):
    """Exporter that writes results to a CSV file."""

    def __init__(self, output_path: str) -> None:
        """Initialize the CSVExporter with a filename.

        Args:
            output_path (str): The path to the CSV file to write to.
        """
        self.output_path = output_path

    @classmethod
    def from_config(cls, config: dict[str, object]) -> Self:
        """Create a CSVExporter from configuration data."""
        return cls(output_path=str(config.get("output_path", "carbon_output.csv")))

    def export(self, run_result: list[RunResult]) -> None:
        """Export the results.

        Args:
            run_result (list[RunResult]): The results to export.
        """
        file_exists = (
            os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 0
        )

        with open(self.output_path, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(
                    [
                        "job_id",
                        "starttime",
                        "runtime",
                        "cputime",
                        "gputime",
                        "memtime",
                        "node",
                        "energy_breakdown_total_kwh",
                        "carbon_intensity",
                        "emissions",
                    ]
                )
            for result in run_result:
                writer.writerow(
                    [
                        result.job.id,
                        result.job.starttime,
                        result.job.runtime,
                        result.job.cputime,
                        result.job.gputime,
                        result.job.memtime,
                        result.node.name,
                        result.energy_breakdown.total,
                        result.carbon_intensity,
                        result.emissions,
                    ]
                )
