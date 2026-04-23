"""Unit tests for sliderule_tool.output."""

from __future__ import annotations

import re
from pathlib import Path
import unittest.mock as mock
from unittest.mock import MagicMock, call, patch

import geopandas as gpd
import pytest
from shapely.geometry import Point

from sliderule_tool.config import Config
from sliderule_tool.exceptions import OutputError
from sliderule_tool.output.formats.csv import write_csv
from sliderule_tool.output.formats.geojson import write_geojson
from sliderule_tool.output.formats.parquet import write_parquet
from sliderule_tool.output.writer import OutputWriter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def gdf() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"value": [1.0, 2.0], "geometry": [Point(0, 0), Point(1, 1)]},
        crs="EPSG:4326",
    )


@pytest.fixture
def config() -> Config:
    return Config(default_output_format="parquet", output_dir=Path("/tmp/sr_test_output"))


@pytest.fixture
def writer(config) -> OutputWriter:
    return OutputWriter(config)


# ---------------------------------------------------------------------------
# OutputWriter.write – format dispatch
# ---------------------------------------------------------------------------


class TestOutputWriterDispatch:
    def test_dispatches_to_parquet(self, writer, gdf, tmp_path):
        dest = tmp_path / "out.parquet"
        mock_fn = mock.MagicMock()
        with patch.dict("sliderule_tool.output.writer._FORMAT_HANDLERS", {"parquet": mock_fn}):
            writer.write(gdf, path=dest, fmt="parquet")
        mock_fn.assert_called_once_with(gdf, dest)

    def test_dispatches_to_geojson(self, writer, gdf, tmp_path):
        dest = tmp_path / "out.geojson"
        mock_fn = mock.MagicMock()
        with patch.dict("sliderule_tool.output.writer._FORMAT_HANDLERS", {"geojson": mock_fn}):
            writer.write(gdf, path=dest, fmt="geojson")
        mock_fn.assert_called_once_with(gdf, dest)

    def test_dispatches_to_csv(self, writer, gdf, tmp_path):
        dest = tmp_path / "out.csv"
        mock_fn = mock.MagicMock()
        with patch.dict("sliderule_tool.output.writer._FORMAT_HANDLERS", {"csv": mock_fn}):
            writer.write(gdf, path=dest, fmt="csv")
        mock_fn.assert_called_once_with(gdf, dest)

    def test_format_is_case_insensitive(self, writer, gdf, tmp_path):
        dest = tmp_path / "out.parquet"
        mock_fn = mock.MagicMock()
        with patch.dict("sliderule_tool.output.writer._FORMAT_HANDLERS", {"parquet": mock_fn}):
            writer.write(gdf, path=dest, fmt="PARQUET")
        mock_fn.assert_called_once()

    def test_unknown_format_raises_output_error(self, writer, gdf, tmp_path):
        with pytest.raises(OutputError, match="Unsupported output format"):
            writer.write(gdf, path=tmp_path / "out.xyz", fmt="xyz")

    def test_returns_path(self, writer, gdf, tmp_path):
        dest = tmp_path / "out.parquet"
        with patch("sliderule_tool.output.writer.write_parquet"):
            result = writer.write(gdf, path=dest, fmt="parquet")
        assert result == dest

    def test_creates_parent_directory(self, writer, gdf, tmp_path):
        dest = tmp_path / "nested" / "dir" / "out.csv"
        with patch("sliderule_tool.output.writer.write_csv"):
            writer.write(gdf, path=dest, fmt="csv")
        assert dest.parent.exists()


# ---------------------------------------------------------------------------
# OutputWriter – auto path generation
# ---------------------------------------------------------------------------


class TestAutoPath:
    def test_auto_path_uses_config_output_dir(self, writer):
        path = writer._auto_path("parquet")
        assert path.parent == Path("/tmp/sr_test_output")

    def test_auto_path_has_correct_extension(self, writer):
        assert writer._auto_path("parquet").suffix == ".parquet"
        assert writer._auto_path("geojson").suffix == ".geojson"
        assert writer._auto_path("csv").suffix == ".csv"

    def test_auto_path_filename_is_timestamp(self, writer):
        path = writer._auto_path("parquet")
        # Pattern: YYYYMMDD_HHMMSS.parquet
        assert re.match(r"\d{8}_\d{6}\.parquet", path.name)

    def test_write_with_no_path_calls_auto_path(self, config, gdf):
        writer = OutputWriter(config)
        with patch.object(writer, "_auto_path", return_value=Path("/tmp/auto.parquet")) as mock_ap:
            with patch("sliderule_tool.output.writer.write_parquet"):
                with patch("pathlib.Path.mkdir"):
                    writer.write(gdf, fmt="parquet")
        mock_ap.assert_called_once_with("parquet")

    def test_write_uses_config_default_format_when_fmt_is_none(self, gdf, tmp_path):
        cfg = Config(default_output_format="csv", output_dir=tmp_path)
        writer = OutputWriter(cfg)
        mock_fn = mock.MagicMock()
        with patch.dict("sliderule_tool.output.writer._FORMAT_HANDLERS", {"csv": mock_fn}):
            path = writer.write(gdf)
        mock_fn.assert_called_once()
        assert path.suffix == ".csv"


# ---------------------------------------------------------------------------
# Format handlers (unit-level, using tmp_path)
# ---------------------------------------------------------------------------


class TestWriteParquet:
    def test_writes_file(self, gdf, tmp_path):
        dest = tmp_path / "test.parquet"
        write_parquet(gdf, dest)
        assert dest.exists()

    def test_raises_output_error_on_failure(self, gdf, tmp_path):
        dest = tmp_path / "test.parquet"
        with patch.object(gdf, "to_parquet", side_effect=OSError("disk full")):
            with pytest.raises(OutputError, match="Failed to write Parquet"):
                write_parquet(gdf, dest)


class TestWriteGeoJSON:
    def test_writes_file(self, gdf, tmp_path):
        dest = tmp_path / "test.geojson"
        write_geojson(gdf, dest)
        assert dest.exists()

    def test_raises_output_error_on_failure(self, gdf, tmp_path):
        dest = tmp_path / "test.geojson"
        with patch.object(gdf, "to_file", side_effect=OSError("no space")):
            with pytest.raises(OutputError, match="Failed to write GeoJSON"):
                write_geojson(gdf, dest)


class TestWriteCSV:
    def test_writes_file(self, gdf, tmp_path):
        dest = tmp_path / "test.csv"
        write_csv(gdf, dest)
        assert dest.exists()

    def test_geometry_converted_to_wkt(self, gdf, tmp_path):
        dest = tmp_path / "test.csv"
        write_csv(gdf, dest)
        content = dest.read_text()
        assert "POINT" in content

    def test_raises_output_error_on_failure(self, gdf, tmp_path):
        dest = tmp_path / "test.csv"
        with patch.object(gpd.GeoDataFrame, "to_csv", side_effect=OSError("no space")):
            with pytest.raises(OutputError, match="Failed to write CSV"):
                write_csv(gdf, dest)

    def test_handles_none_geometry(self, tmp_path):
        gdf_none = gpd.GeoDataFrame(
            {"value": [1], "geometry": [None]}, crs="EPSG:4326"
        )
        dest = tmp_path / "test_none.csv"
        write_csv(gdf_none, dest)
        assert dest.exists()
