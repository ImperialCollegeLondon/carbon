"""Unit tests for the CarbonIntensity class."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from carbon.clusterconfig import ClusterConfig
from carbon.intensity import CarbonIntensity

with open(Path("clusters/dummy.yaml")) as f:
    TEST_CONFIG = yaml.safe_load(f)
config = ClusterConfig(**TEST_CONFIG)
region_id = config.region_id


def test_carbon_intensity_init() -> None:
    """Test CarbonIntensity initialization."""
    dt = datetime(2025, 8, 21, 12, 0, 0)
    ci = CarbonIntensity(dt, region_id)
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
        ci = CarbonIntensity(dt, region_id)
        assert ci.fetch() == 120.0
