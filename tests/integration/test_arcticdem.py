"""Integration tests for the ArcticDEM dataset.

These tests require a live internet connection to ``slideruleearth.io``.
Run them with::

    pytest -m integration tests/integration/

They are skipped by default in CI environments where the SlideRule API is
not reachable.
"""

from __future__ import annotations

import pytest

from sliderule_tool.config import Config
from sliderule_tool.core.client import SlideRuleClient
from sliderule_tool.core.region import RegionOfInterest
from sliderule_tool.datasets import get_dataset
from sliderule_tool.datasets.arcticdem.params import ArcticDEMParams, ArcticDEMSamplingParams

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
# ArcticDEM co-sampling (default mosaic)
# ---------------------------------------------------------------------------


class TestArcticDEMMosaicIntegration:
    def test_fetch_returns_geodataframe(self, live_client, live_config, small_alaska_region):
        import geopandas as gpd

        params = ArcticDEMParams(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("arcticdem", live_config)
        gdf = dataset.fetch(params)
        assert isinstance(gdf, gpd.GeoDataFrame)

    def test_fetch_returns_non_empty_dataframe(self, live_client, live_config, small_alaska_region):
        params = ArcticDEMParams(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("arcticdem", live_config)
        gdf = dataset.fetch(params)
        assert len(gdf) > 0, "Expected non-empty GeoDataFrame for ArcticDEM"

    def test_result_has_arcticdem_columns(self, live_client, live_config, small_alaska_region):
        """ArcticDEM co-sampling should add columns prefixed with 'arcticdem-mosaic'."""
        params = ArcticDEMParams(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
            sampling=ArcticDEMSamplingParams(asset="arcticdem-mosaic", radius=10.0),
        )
        dataset = get_dataset("arcticdem", live_config)
        gdf = dataset.fetch(params)
        arcticdem_cols = [c for c in gdf.columns if "arcticdem" in c.lower()]
        assert len(arcticdem_cols) > 0, (
            f"Expected ArcticDEM columns in result, got: {list(gdf.columns)}"
        )

    def test_result_has_geometry_column(self, live_client, live_config, small_alaska_region):
        params = ArcticDEMParams(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("arcticdem", live_config)
        gdf = dataset.fetch(params)
        assert "geometry" in gdf.columns


# ---------------------------------------------------------------------------
# ArcticDEM strips asset
# ---------------------------------------------------------------------------


class TestArcticDEMStripsIntegration:
    def test_fetch_with_strips_returns_geodataframe(
        self, live_client, live_config, small_alaska_region
    ):
        import geopandas as gpd

        params = ArcticDEMParams(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
            sampling=ArcticDEMSamplingParams(asset="arcticdem-strips", radius=15.0),
        )
        dataset = get_dataset("arcticdem", live_config)
        gdf = dataset.fetch(params)
        assert isinstance(gdf, gpd.GeoDataFrame)


# ---------------------------------------------------------------------------
# run() method (end-to-end with file output)
# ---------------------------------------------------------------------------


class TestRunMethodIntegration:
    def test_run_writes_parquet(self, live_client, live_config, small_alaska_region, tmp_path):
        params = ArcticDEMParams(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("arcticdem", live_config)
        out_path = tmp_path / "arcticdem_result.parquet"
        gdf = dataset.run(params, output_path=out_path, output_format="parquet")
        assert out_path.exists()
        assert len(gdf) > 0

    def test_run_returns_geodataframe_without_output(
        self, live_client, live_config, small_alaska_region
    ):
        import geopandas as gpd

        params = ArcticDEMParams(
            region=small_alaska_region,
            t0="2021-01-01",
            t1="2021-03-31",
        )
        dataset = get_dataset("arcticdem", live_config)
        gdf = dataset.run(params)
        assert isinstance(gdf, gpd.GeoDataFrame)


# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------


def test_arcticdem_in_dataset_registry():
    from sliderule_tool.datasets import list_datasets
    assert "arcticdem" in list_datasets()


def test_get_arcticdem_dataset(live_config):
    dataset = get_dataset("arcticdem", live_config)
    assert dataset.name == "arcticdem"


def test_list_datasets_contains_both(live_config):
    from sliderule_tool.datasets import list_datasets
    datasets = list_datasets()
    assert "icesat2" in datasets
    assert "arcticdem" in datasets
