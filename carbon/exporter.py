"""The carbon exporter module.

This module provides functionality to fetch and display carbon intensity data.
Data is fetched from the Carbon Intensity API (carbonintensity.org.uk) based on the
specified region and time period.
"""

import csv
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Self

from . import RunResult
from .clusterconfig import CSVExporterConfig


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
            run_result: The results to export.
        """


@dataclass
class CSVExporter(Exporter):
    """Exporter that writes results to a CSV file."""

    output_path: Path
    """Path where CSV output will be saved."""

    @classmethod
    def from_config(cls, config: dict[str, object]) -> Self:
        """Create a CSVExporter from configuration data."""
        validated_config = CSVExporterConfig.model_validate(config)
        return cls(output_path=validated_config.output_path)

    def export(self, run_result: list[RunResult]) -> None:
        """Export the results.

        Args:
            run_result: The results to export.
        """
        fieldnames = [
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
        with open(self.output_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in run_result:
                writer.writerow(
                    dict(
                        job_id=result.job.id,
                        starttime=result.job.starttime,
                        runtime=result.job.runtime,
                        cputime=result.job.cputime,
                        gputime=result.job.gputime,
                        memtime=result.job.memtime,
                        node=result.node.name,
                        energy_breakdown_total_kwh=result.energy_breakdown.total,
                        carbon_intensity=result.carbon_intensity,
                        emissions=result.emissions,
                    )
                )
