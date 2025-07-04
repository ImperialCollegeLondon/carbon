"""The carbon intensity module.

This module provides functionality to fetch and display carbon intensity data.
Data is fetched from the Carbon Intensity API (carbonintensity.org.uk) based on the
specified region and time period.
"""

from datetime import datetime, timedelta

import requests


class CarbonIntensity:
    """A class to represent carbon intensity data."""

    REGIONID = 13  # London region ID for carbon intensity API

    def __init__(self, time: datetime) -> None:
        """Initialize the CarbonIntensity object.

        Args:
            time: The time for which to fetch carbon intensity data.
        """
        self._stime = time.strftime("%Y-%m-%dT%H:%MZ")
        self._stime_plus = (time + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%MZ")

    def fetch(self) -> float:
        """Fetch carbon intensity data."""
        headers = {"Accept": "application/json"}
        response = requests.get(
            f"https://api.carbonintensity.org.uk/regional/intensity/{self._stime}/{self._stime_plus}/regionid/{self.REGIONID}",
            params={},
            headers=headers,
        )

        if response.status_code != 200:
            raise ValueError(
                f"Failed to fetch carbon intensity data: "
                f"{response.status_code} {response.text}"
            )

        # We ask for a 30 minute time period, so
        # should only be one item in the data list
        # which we select with `next(iter(...)).
        # Can only get forecasted data for regions
        intensity = next(iter(response.json()["data"]["data"]))["intensity"]["forecast"]

        return float(intensity)
