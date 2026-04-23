"""Integration tests for the ICESat-2 dataset.

These tests require a live internet connection to ``slideruleearth.io``.
Run them with::

    pytest -m integration tests/integration/

or with the ``--run-integration`` flag if configured in ``pyproject.toml``.

They are skipped by default in CI environments where the SlideRule API is
not reachable.
"""

from __future__ import annotations

import pytest

from sliderule_tool.config import Config
from sliderule_tool.core.client import SlideRuleClient
from sliderule_tool.core.region import RegionOfInterest
from sliderule_tool.datasets import get_dataset
from sliderule_tool.datasets.icesat2.params import ATL06Params, ATL03Params, ATL08Params

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def live_config() -> Config:
    """Return a Config for live API testing."""
    return Config.load()


@pytest.fixture(scope="module")
def live_client(live_config) -> SlideRuleClient:
    """Initialise a live SlideRule session for the module duration."""
    client = SlideRuleClient(live_config)
    client.initialize()
    yield client
    client.shutdown()


@pytest.fixture(scope="module")
def small_alaska_region() -> RegionOfInterest:
    """A small region over interior Alaska suitable for short integration tests."""
    return RegionOfInterest.from_bbox(-150.5, 69.0, -148.5, 70.0)


# ---------------------------------------------------------------------------
# ATL06 (land-ice elevation)
# ---------------------------------------------------------------------------


class TestATL06Integration:
    def test_fetch_returns_geodataframe(self, live_client, live_config, small_alaska_region):
        import geopandas as gpd

        params = ATL06Params(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("icesat2", live_config)
        gdf = dataset.fetch(params, product="atl06")
        assert isinstance(gdf, gpd.GeoDataFrame)

    def test_fetch_returns_non_empty_dataframe(self, live_client, live_config, small_alaska_region):
        params = ATL06Params(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("icesat2", live_config)
        gdf = dataset.fetch(params, product="atl06")
        assert len(gdf) > 0, "Expected non-empty GeoDataFrame for ATL06"

    def test_fetch_has_geometry_column(self, live_client, live_config, small_alaska_region):
        params = ATL06Params(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("icesat2", live_config)
        gdf = dataset.fetch(params, product="atl06")
        assert "geometry" in gdf.columns

    def test_fetch_has_height_column(self, live_client, live_config, small_alaska_region):
        """ATL06 results should contain an elevation / height column."""
        params = ATL06Params(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("icesat2", live_config)
        gdf = dataset.fetch(params, product="atl06")
        # Column name is 'h_mean' in ATL06 SlideRule output
        assert "h_mean" in gdf.columns, f"Columns: {list(gdf.columns)}"


# ---------------------------------------------------------------------------
# ATL03 (photon-level)
# ---------------------------------------------------------------------------


class TestATL03Integration:
    def test_fetch_atl03_returns_geodataframe(self, live_client, live_config, small_alaska_region):
        import geopandas as gpd

        params = ATL03Params(
            region=small_alaska_region,
            t0="2021-01-15",
            t1="2021-01-31",
            cnt=5,
        )
        dataset = get_dataset("icesat2", live_config)
        gdf = dataset.fetch(params, product="atl03")
        assert isinstance(gdf, gpd.GeoDataFrame)


# ---------------------------------------------------------------------------
# ATL08 (vegetation / canopy)
# ---------------------------------------------------------------------------


class TestATL08Integration:
    def test_fetch_atl08_returns_geodataframe(self, live_client, live_config, small_alaska_region):
        import geopandas as gpd

        params = ATL08Params(
            region=small_alaska_region,
            t0="2021-06-01",
            t1="2021-08-31",
            atl08_class=["atl08_ground", "atl08_canopy"],
        )
        dataset = get_dataset("icesat2", live_config)
        gdf = dataset.fetch(params, product="atl08")
        assert isinstance(gdf, gpd.GeoDataFrame)


# ---------------------------------------------------------------------------
# run() method (end-to-end with optional file output)
# ---------------------------------------------------------------------------


class TestRunMethodIntegration:
    def test_run_writes_parquet(self, live_client, live_config, small_alaska_region, tmp_path):
        params = ATL06Params(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("icesat2", live_config)
        out_path = tmp_path / "atl06_result.parquet"
        gdf = dataset.run(params, output_path=out_path, output_format="parquet")
        assert out_path.exists()
        assert len(gdf) > 0

    def test_run_writes_geojson(self, live_client, live_config, small_alaska_region, tmp_path):
        params = ATL06Params(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("icesat2", live_config)
        out_path = tmp_path / "atl06_result.geojson"
        gdf = dataset.run(params, output_path=out_path, output_format="geojson")
        assert out_path.exists()


# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------


def test_icesat2_in_dataset_registry():
    from sliderule_tool.datasets import list_datasets
    assert "icesat2" in list_datasets()


def test_get_icesat2_dataset(live_config):
    dataset = get_dataset("icesat2", live_config)
    assert dataset.name == "icesat2"
