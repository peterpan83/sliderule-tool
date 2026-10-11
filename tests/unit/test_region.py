"""Unit tests for sliderule_tool.core.region."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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
        # sliderule.toregion() rejects a raw GeoJSON Feature dict, so from_bbox
        # must hand it a GeoDataFrame in EPSG:4326 covering exactly the bbox.
        import geopandas as gpd
        from shapely.geometry import box

        RegionOfInterest.from_bbox(-105.3, 68.95, -104.8, 69.15)
        gdf = mock_toregion.call_args[0][0]
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert gdf.crs.to_epsg() == 4326
        assert len(gdf) == 1
        assert gdf.geometry.iloc[0].equals(box(-105.3, 68.95, -104.8, 69.15))

    def test_bbox_wraps_exception_in_region_error(self):
        with patch("sliderule_tool.core.region.sr.toregion", side_effect=RuntimeError("boom")):
            with pytest.raises(RegionError, match="Failed to create region from bbox"):
                RegionOfInterest.from_bbox(0.0, 0.0, 1.0, 1.0)

    @pytest.mark.parametrize(
        "bbox",
        [
            (170.0, 60.0, -170.0, 70.0),  # crosses the antimeridian
            (68.95, -105.3, 69.15, -104.8),  # lat/lon swapped
            (0.0, 1.0, 1.0, 0.0),  # south > north
            (0.0, 0.0, 0.0, 1.0),  # zero width
            (0.0, 1.0, 1.0, 1.0),  # zero height
            (-181.0, 0.0, 1.0, 1.0),  # lon out of range
            (0.0, 0.0, 1.0, 91.0),  # lat out of range
            (float("nan"), 0.0, 1.0, 1.0),
            ("0", 0.0, 1.0, 1.0),
        ],
    )
    def test_invalid_bbox_raises_before_toregion(self, mock_toregion, bbox):
        with pytest.raises(RegionError, match="Invalid bbox"):
            RegionOfInterest.from_bbox(*bbox)
        mock_toregion.assert_not_called()

    def test_full_globe_bbox_is_valid(self, mock_toregion):
        RegionOfInterest.from_bbox(-180.0, -90.0, 180.0, 90.0)
        mock_toregion.assert_called_once()


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
# equality
# ---------------------------------------------------------------------------


class TestEquality:
    def test_equal_when_poly_and_raster_match(self):
        import geopandas as gpd

        # Real toregion() output carries a GeoDataFrame under "gdf"; comparing
        # it element-wise used to raise "truth value of a DataFrame is ambiguous".
        a = RegionOfInterest(_raw={**_raw(_make_poly()), "gdf": gpd.GeoDataFrame({"x": [1]})})
        b = RegionOfInterest(_raw={**_raw(_make_poly()), "gdf": gpd.GeoDataFrame({"x": [1]})})
        assert a == b

    def test_unequal_when_poly_differs(self):
        assert RegionOfInterest(_raw=_raw(_make_poly(5))) != RegionOfInterest(
            _raw=_raw(_make_poly(6))
        )

    def test_not_equal_to_other_types(self):
        assert RegionOfInterest(_raw=_raw(_make_poly())) != _raw(_make_poly())


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
