"""The carbon intensity module.

This module provides functionality to fetch and display carbon intensity data.
Data is fetched from the Carbon Intensity API (carbonintensity.org.uk) based on the
specified region and time period.
"""

from datetime import datetime, timedelta

import requests


class CarbonIntensity:
    """Represents carbon intensity data.

    Represents carbon intensity data and provides methods to fetch carbon intensity
    for a given time and region from the Carbon Intensity API.

    Attributes:
        region_id (int): The region ID for the API.
        _stime (str): Start time in ISO format for the API query.
        _stime_plus (str): End time in ISO format for the API query.
    """

    def __init__(self, time: datetime, region_id: int) -> None:
        """Initialize the CarbonIntensity object.

        Args:
            time (datetime): The time for which to fetch carbon intensity data.
            region_id (int): The region ID for the API.
        """
        self.region_id = region_id
        self._stime = time.strftime("%Y-%m-%dT%H:%MZ")
        self._stime_plus = (time + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%MZ")

    def fetch(self) -> float:
        """Fetch carbon intensity data from the API for the specified time and region.

        Returns:
            float: The forecasted carbon intensity in gCO2/kWh.

        Raises:
            ValueError: If the API request fails or returns an error status.
        """
        headers = {"Accept": "application/json"}
        response = requests.get(
            f"https://api.carbonintensity.org.uk/regional/intensity/{self._stime}/{self._stime_plus}/regionid/{self.region_id}",
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
