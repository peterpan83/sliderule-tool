"""Unit tests for sliderule_tool.core.region."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import geopandas as gpd
import pytest

from sliderule_tool.core.region import RegionOfInterest
from sliderule_tool.exceptions import RegionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_poly(n: int = 5) -> list[dict]:
    """Return a synthetic polygon with *n* vertices."""
    return [{"lon": float(i), "lat": float(i)} for i in range(n)]


def _raw(poly: list[dict]) -> dict:
    return {"poly": poly, "raster": {}}


# ---------------------------------------------------------------------------
# from_bbox
# ---------------------------------------------------------------------------


class TestFromBbox:
    def test_returns_region_of_interest(self, mock_toregion):
        roi = RegionOfInterest.from_bbox(-150.5, 69.0, -148.5, 70.0)
        assert isinstance(roi, RegionOfInterest)

    def test_poly_has_five_vertices(self, mock_toregion, alaska_poly):
        roi = RegionOfInterest.from_bbox(-150.5, 69.0, -148.5, 70.0)
        assert len(roi.poly) == 5

    def test_poly_values_match_mock(self, mock_toregion, alaska_poly):
        roi = RegionOfInterest.from_bbox(-150.5, 69.0, -148.5, 70.0)
        assert roi.poly == alaska_poly

    def test_toregion_called_with_geodataframe(self, mock_toregion):
        RegionOfInterest.from_bbox(0.0, 0.0, 1.0, 1.0)
        call_args = mock_toregion.call_args[0][0]
        assert isinstance(call_args, gpd.GeoDataFrame)
        assert call_args.geometry.iloc[0].geom_type == "Polygon"
        assert call_args.total_bounds.tolist() == [0.0, 0.0, 1.0, 1.0]

    def test_bbox_wraps_exception_in_region_error(self):
        with patch("sliderule_tool.core.region.sr.toregion", side_effect=RuntimeError("boom")):
            with pytest.raises(RegionError, match="Failed to create region from bbox"):
                RegionOfInterest.from_bbox(0.0, 0.0, 1.0, 1.0)


# ---------------------------------------------------------------------------
# from_geojson
# ---------------------------------------------------------------------------


class TestFromGeoJSON:
    def test_returns_region_of_interest(self, mock_toregion):
        roi = RegionOfInterest.from_geojson("/fake/path.geojson")
        assert isinstance(roi, RegionOfInterest)

    def test_toregion_called_with_string_path(self, mock_toregion):
        RegionOfInterest.from_geojson("/fake/path.geojson")
        mock_toregion.assert_called_once_with("/fake/path.geojson")

    def test_wraps_exception_in_region_error(self):
        with patch("sliderule_tool.core.region.sr.toregion", side_effect=FileNotFoundError("no")):
            with pytest.raises(RegionError, match="Failed to load region from GeoJSON"):
                RegionOfInterest.from_geojson("/nonexistent.geojson")


# ---------------------------------------------------------------------------
# from_shapefile
# ---------------------------------------------------------------------------


class TestFromShapefile:
    def test_returns_region_of_interest(self, mock_toregion):
        roi = RegionOfInterest.from_shapefile("/fake/path.shp")
        assert isinstance(roi, RegionOfInterest)

    def test_wraps_exception_in_region_error(self):
        with patch("sliderule_tool.core.region.sr.toregion", side_effect=OSError("no")):
            with pytest.raises(RegionError, match="Failed to load region from shapefile"):
                RegionOfInterest.from_shapefile("/nonexistent.shp")


# ---------------------------------------------------------------------------
# from_geodataframe
# ---------------------------------------------------------------------------


class TestFromGeoDataFrame:
    def test_returns_region_of_interest(self, mock_toregion):
        import geopandas as gpd

        gdf = gpd.GeoDataFrame()
        roi = RegionOfInterest.from_geodataframe(gdf)
        assert isinstance(roi, RegionOfInterest)

    def test_wraps_exception_in_region_error(self):
        import geopandas as gpd

        with patch("sliderule_tool.core.region.sr.toregion", side_effect=ValueError("bad")):
            with pytest.raises(RegionError, match="Failed to load region from GeoDataFrame"):
                RegionOfInterest.from_geodataframe(gpd.GeoDataFrame())


# ---------------------------------------------------------------------------
# poly property
# ---------------------------------------------------------------------------


class TestPolyProperty:
    def test_poly_returns_list(self, mock_toregion):
        roi = RegionOfInterest.from_bbox(0.0, 0.0, 1.0, 1.0)
        assert isinstance(roi.poly, list)

    def test_poly_fallback_when_no_poly_key(self):
        # If toregion returns a plain list (older API), poly should still work
        raw_list = [{"lon": 0.0, "lat": 0.0}] * 5
        roi = RegionOfInterest(_raw=raw_list)
        # raw_list.get() doesn't exist on a list, so poly returns _raw directly
        # We test the dataclass directly with a dict lacking 'poly'
        raw_dict = {"lon_list": []}
        roi2 = RegionOfInterest(_raw=raw_dict)
        # get() with default returns _raw itself when 'poly' key missing
        assert roi2.poly == raw_dict


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_valid_region_does_not_raise(self, mock_toregion):
        roi = RegionOfInterest.from_bbox(0.0, 0.0, 1.0, 1.0)
        roi.validate()  # should not raise

    def test_empty_poly_raises(self):
        roi = RegionOfInterest(_raw={"poly": []})
        with pytest.raises(RegionError, match="at least 4 vertices"):
            roi.validate()

    def test_too_few_vertices_raises(self):
        roi = RegionOfInterest(_raw={"poly": _make_poly(3)})
        with pytest.raises(RegionError, match="at least 4 vertices"):
            roi.validate()

    def test_exactly_four_vertices_is_valid(self):
        roi = RegionOfInterest(_raw={"poly": _make_poly(4)})
        roi.validate()  # should not raise

    def test_five_vertices_is_valid(self):
        roi = RegionOfInterest(_raw={"poly": _make_poly(5)})
        roi.validate()  # should not raise
