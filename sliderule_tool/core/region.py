"""Region-of-interest helpers that wrap ``sliderule.toregion()``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import sliderule as sr
from shapely.geometry import box

from sliderule_tool.exceptions import RegionError


@dataclass(eq=False)
class RegionOfInterest:
    """Wraps the output of ``sliderule.toregion()`` for convenient polygon access.

    The underlying ``_raw`` dict has the shape returned by ``sliderule.toregion()``:
    ``{"poly": [{"lon": x, "lat": y}, ...], "raster": {...}}``.
    """

    _raw: dict  # output of sliderule.toregion()

    def __eq__(self, other: object) -> bool:
        # ``_raw`` may hold a GeoDataFrame under "gdf", whose ``==`` is
        # element-wise, so compare only the parts sent to SlideRule.
        if not isinstance(other, RegionOfInterest):
            return NotImplemented
        return self.poly == other.poly and self.raster == other.raster

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_geojson(cls, path: Path | str) -> RegionOfInterest:
        """Load a region from a GeoJSON file.

        Args:
            path: Filesystem path to a ``.geojson`` / ``.json`` file.

        Returns:
            A new :class:`RegionOfInterest` instance.

        Raises:
            RegionError: If the file cannot be loaded or parsed.
        """
        try:
            raw = sr.toregion(str(path))
            return cls(_raw=raw)
        except Exception as e:
            raise RegionError(f"Failed to load region from GeoJSON: {path}") from e

    @classmethod
    def from_shapefile(cls, path: Path | str) -> RegionOfInterest:
        """Load a region from a shapefile.

        Args:
            path: Filesystem path to a ``.shp`` file.

        Returns:
            A new :class:`RegionOfInterest` instance.

        Raises:
            RegionError: If the file cannot be loaded or parsed.
        """
        try:
            raw = sr.toregion(str(path))
            return cls(_raw=raw)
        except Exception as e:
            raise RegionError(f"Failed to load region from shapefile: {path}") from e

    @classmethod
    def from_geodataframe(cls, gdf: gpd.GeoDataFrame) -> RegionOfInterest:
        """Load a region from an in-memory GeoDataFrame.

        Args:
            gdf: A GeoDataFrame whose geometry defines the region.

        Returns:
            A new :class:`RegionOfInterest` instance.

        Raises:
            RegionError: If the GeoDataFrame cannot be converted.
        """
        try:
            raw = sr.toregion(gdf)
            return cls(_raw=raw)
        except Exception as e:
            raise RegionError("Failed to load region from GeoDataFrame") from e

    @classmethod
    def from_bbox(
        cls,
        west: float,
        south: float,
        east: float,
        north: float,
    ) -> RegionOfInterest:
        """Create a rectangular region from bounding-box coordinates.

        Args:
            west: Western longitude boundary.
            south: Southern latitude boundary.
            east: Eastern longitude boundary.
            north: Northern latitude boundary.

        Returns:
            A new :class:`RegionOfInterest` instance.

        Raises:
            RegionError: If the bounding box is out of range, empty, crosses the
                antimeridian (``west > east``), or cannot be converted.
        """
        try:
            valid = -180 <= west < east <= 180 and -90 <= south < north <= 90
        except TypeError:
            valid = False
        if not valid:
            raise RegionError(
                f"Invalid bbox ({west},{south},{east},{north}): need "
                "-180 <= west < east <= 180 and -90 <= south < north <= 90 "
                "(antimeridian-crossing boxes are not supported)"
            )

        # sliderule.toregion() does not accept a raw GeoJSON Feature dict;
        # hand it a GeoDataFrame and let it handle polygon winding.
        try:
            gdf = gpd.GeoDataFrame(geometry=[box(west, south, east, north)], crs="EPSG:4326")
            raw = sr.toregion(gdf)
            return cls(_raw=raw)
        except Exception as e:
            raise RegionError(
                f"Failed to create region from bbox ({west},{south},{east},{north})"
            ) from e

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def poly(self) -> list[dict]:
        """Return the polygon as a list of ``{"lon": x, "lat": y}`` dicts."""
        return self._raw.get("poly", self._raw)

    @property
    def raster(self) -> dict | None:
        """Return the rasterized region used for efficient server-side filtering.

        ``sliderule.toregion()`` returns this alongside ``poly``.  SlideRule
        recommends passing it for complex polygons (>100–200 vertices) to
        avoid performance degradation from vertex-by-vertex filtering.
        Returns ``None`` when the raw dict does not contain a raster entry.
        """
        return self._raw.get("raster") or None

    @property
    def is_complex(self) -> bool:
        """Return ``True`` when the polygon has more than 100 vertices."""
        return len(self.poly) > 100

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Validate that the region polygon has sufficient vertices.

        Raises:
            RegionError: If the polygon has fewer than 4 vertices.
        """
        poly = self.poly
        if not poly or len(poly) < 4:
            raise RegionError(
                "Region polygon must have at least 4 vertices (including closing vertex)"
            )
