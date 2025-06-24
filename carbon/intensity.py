"""The carbon intensity module.

This module provides functionality to fetch and display carbon intensity data.
Data is fetched from the Carbon Intensity API (carbonintensity.org.uk) based on the
specified region and time period.
"""

from datetime import datetime, timedelta

import requests


class CarbonIntensity:
    """A class to represent carbon intensity data."""

    def __init__(self) -> None:
        """Initialize the CarbonIntensity object."""
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%MZ"
        )

    def get_yesterday(self) -> int:
        """Fetch carbon intensity data for yesterday."""
        headers = {"Accept": "application/json"}
        response = requests.get(
            f"https://api.carbonintensity.org.uk/intensity/{self.yesterday}",
            params={},
            headers=headers,
        )
        return response.json()["data"][0]["intensity"]["actual"]
