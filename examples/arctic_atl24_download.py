"""Download ICESat-2 ATL24 bathymetry for an Arctic coastal polygon.

Area of interest: Beaufort Sea coast, northern Alaska
(shallow nearshore waters between Prudhoe Bay and the Canada border)

Run:
    python examples/arctic_atl24_download.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon

from sliderule_tool import SlideRuleTool, RegionOfInterest
from sliderule_tool.datasets.icesat2.params import ATL24Params

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Area of interest — arbitrary polygon, Beaufort Sea coast, northern Alaska
#
#  +---------+
#  |         |  Arctic Ocean / Beaufort Sea
#  |   ~~~~~  <- coastline
#  +--+   +--+
#     | * |      * = nearshore shallow water targeted by ATL24
#     +---+
#
# Vertices go counter-clockwise.  The shape cuts inland slightly near
# Prudhoe Bay and stays within the nearshore zone (<30 km offshore).
# ---------------------------------------------------------------------------
AOI_POLYGON = Polygon([
    (-148.0, 70.2),   # near Prudhoe Bay, slightly inland
    (-149.5, 70.5),   # offshore to the west
    (-151.0, 70.8),   # further west, deeper into Beaufort Sea
    (-152.5, 70.9),   # westernmost point
    (-152.5, 71.3),   # north, open water
    (-148.0, 71.3),   # northeast corner
    (-148.0, 70.2),   # close polygon
])

OUTPUT_PATH = Path(__file__).parent.parent / "output" / "arctic_beaufort_atl24.parquet"
T0 = "2024-07-01"
T1 = "2025-07-01"


def build_region(polygon: Polygon) -> RegionOfInterest:
    """Convert a Shapely polygon to a RegionOfInterest."""
    gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")
    return RegionOfInterest.from_geodataframe(gdf)


def main() -> None:
    logger.info("Building AOI — Beaufort Sea coast, northern Alaska")
    region = build_region(AOI_POLYGON)
    logger.info("Polygon vertices: %d", len(region.poly))
    logger.info("Using raster filter: %s", region.raster is not None)

    params = ATL24Params(
        region=region,
        t0=T0,
        t1=T1,
        atl24_class=["bathymetry", "sea_surface"],
        len=40.0,   # along-track extent length (metres)
        res=20.0,   # spacing between extent centres (metres)
    )

    logger.info("Fetching ATL24 bathymetry  %s → %s", T0, T1)

    with SlideRuleTool() as tool:
        gdf = tool.fetch(
            dataset="icesat2",
            product="atl24",
            region=region,
            t0=T0,
            t1=T1,
            atl24_class=["bathymetry", "sea_surface"],
            len=40.0,
            res=20.0,
            output_path=OUTPUT_PATH,
        )

    if gdf.empty:
        logger.warning("No data returned — try widening the AOI or date range.")
        return

    logger.info("Downloaded %d records", len(gdf))
    logger.info("Columns: %s", gdf.columns.tolist())
    logger.info("Saved to %s", OUTPUT_PATH.resolve())

    # Quick summary
    if "height" in gdf.columns:
        logger.info(
            "Height range: %.2f m to %.2f m",
            gdf["height"].min(),
            gdf["height"].max(),
        )
    print(gdf.head())


if __name__ == "__main__":
    main()
