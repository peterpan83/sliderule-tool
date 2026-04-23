"""Shared pytest fixtures for sliderule-tool tests.

All fixtures that interact with ``sliderule.toregion`` use
``unittest.mock.patch`` so that unit tests run without a live SlideRule
connection or the ``sliderule`` package installed.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sliderule_tool.config import Config


# ---------------------------------------------------------------------------
# Config fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config() -> Config:
    """Return a default :class:`~sliderule_tool.config.Config` instance."""
    return Config()


@pytest.fixture
def custom_config() -> Config:
    """Return a :class:`~sliderule_tool.config.Config` with custom values."""
    return Config(
        api_url="test.slideruleearth.io",
        organization="test-org",
        desired_nodes=4,
        timeout=120,
        max_resources=500,
        default_output_format="geojson",
        output_dir=Path("/tmp/test_output"),
        log_level="DEBUG",
    )


# ---------------------------------------------------------------------------
# Region fixtures (mocked to avoid live sliderule dependency)
# ---------------------------------------------------------------------------

# Canonical polygon returned by mocked sliderule.toregion() for a bbox over
# Alaska: corners + closing vertex, matching the from_bbox() implementation.
_ALASKA_POLY = [
    {"lon": -150.5, "lat": 69.0},
    {"lon": -148.5, "lat": 69.0},
    {"lon": -148.5, "lat": 70.0},
    {"lon": -150.5, "lat": 70.0},
    {"lon": -150.5, "lat": 69.0},
]

_MOCK_TOREGION_RETURN = {"poly": _ALASKA_POLY, "raster": {}}


@pytest.fixture
def mock_toregion():
    """Patch ``sliderule.toregion`` so unit tests don't need sliderule installed.

    Yields the mock object for further customisation in individual tests.
    """
    with patch("sliderule_tool.core.region.sr.toregion", return_value=_MOCK_TOREGION_RETURN) as m:
        yield m


@pytest.fixture
def alaska_region(mock_toregion):
    """Return a :class:`~sliderule_tool.core.region.RegionOfInterest` over Alaska.

    Depends on ``mock_toregion`` so that no live connection is required.
    """
    from sliderule_tool.core.region import RegionOfInterest

    return RegionOfInterest.from_bbox(-150.5, 69.0, -148.5, 70.0)


@pytest.fixture
def alaska_poly() -> list[dict]:
    """Return the raw polygon list for the Alaska test region."""
    return _ALASKA_POLY


# ---------------------------------------------------------------------------
# GeoDataFrame fixture (minimal, geometry-free for output tests)
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_gdf():
    """Return a minimal GeoDataFrame with a Point geometry column."""
    import geopandas as gpd
    from shapely.geometry import Point

    return gpd.GeoDataFrame(
        {
            "value": [1.0, 2.0, 3.0],
            "label": ["a", "b", "c"],
            "geometry": [Point(0, 0), Point(1, 1), Point(2, 2)],
        },
        crs="EPSG:4326",
    )
