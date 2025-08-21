"""Unit tests for the CarbonIntensity class."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from carbon.intensity import CarbonIntensity


def test_carbon_intensity_init() -> None:
    """Test CarbonIntensity initialization."""
    dt = datetime(2025, 8, 21, 12, 0, 0)
    ci = CarbonIntensity(dt)
    assert ci._stime.startswith("2025-08-21T12:00")
    assert ci._stime_plus.startswith("2025-08-21T12:30")


@pytest.fixture
def mock_response() -> Mock:
    """Fixture for a mocked API response object."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "data": {"data": [{"intensity": {"forecast": 120.0}}]}
    }
    return response


def test_carbon_intensity_fetch(mock_response) -> None:
    """Test CarbonIntensity.fetch() with mocked API response."""
    with patch("requests.get", return_value=mock_response):
        dt = datetime(2025, 8, 21, 12, 0, 0)
        ci = CarbonIntensity(dt)
        assert ci.fetch() == 120.0
