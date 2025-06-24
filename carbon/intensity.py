"""The carbon intensity module.

This module provides functionality to fetch and display carbon intensity data.
Data is fetched from the Carbon Intensity API (carbonintensity.org.uk) based on the
specified region and time period.
"""

from datetime import datetime

import requests


class CarbonIntensity:
    """A class to represent carbon intensity data."""

    def __init__(self, time: datetime) -> None:
        """Initialize the CarbonIntensity object.

        Args:
            time: The time for which to fetch carbon intensity data.
        """
        self._time = time.strftime("%Y-%m-%dT%H:%MZ")

    def fetch(self) -> float:
        """Fetch carbon intensity data."""
        headers = {"Accept": "application/json"}
        response = requests.get(
            f"https://api.carbonintensity.org.uk/intensity/{self._time}",
            params={},
            headers=headers,
        )

        if response.status_code != 200:
            raise ValueError(
                f"Failed to fetch carbon intensity data: "
                f"{response.status_code} {response.text}"
            )

        intensity = response.json()["data"][0]["intensity"]["actual"]
        if intensity is None:
            # ToDo: add a info message to indicate we are using forecasted data.
            # Maybe implement a logger?
            intensity = response.json()["data"][0]["intensity"]["forecast"]

        return float(intensity)
