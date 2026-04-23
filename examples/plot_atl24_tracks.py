"""Plot ICESat-2 ATL24 bathymetry track lines on a Google Earth satellite basemap.

Reads output/arctic_beaufort_atl24.parquet, converts photon points to
per-beam track lines, colours them by seafloor depth (ortho_h), and
overlays the AOI polygon.

Run:
    python examples/plot_atl24_tracks.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe in all environments
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.collections as mcoll
import numpy as np
from shapely.geometry import LineString, Polygon

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PARQUET = Path(__file__).parent.parent / "output" / "arctic_beaufort_atl24.parquet"
OUTPUT  = Path(__file__).parent.parent / "output" / "arctic_beaufort_atl24_tracks.png"

# AOI polygon (same as download script)
AOI_POLYGON = Polygon([
    (-148.0, 70.2),
    (-149.5, 70.5),
    (-151.0, 70.8),
    (-152.5, 70.9),
    (-152.5, 71.3),
    (-148.0, 71.3),
    (-148.0, 70.2),
])

# Google satellite XYZ tile URL (no API key required for tile access)
GOOGLE_SAT = (
    "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"  # satellite + labels
)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_parquet(path)
    # The stored CRS is a CompoundCRS (ITRF2014 + EGM2008); override the
    # horizontal component to plain WGS-84 so reprojection works cleanly.
    gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf


# ---------------------------------------------------------------------------
# Build track lines: one LineString per (rgt, cycle, gt) beam pass
# ---------------------------------------------------------------------------
def points_to_tracks(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    records = []
    for (rgt, cycle, gt), grp in gdf.groupby(["rgt", "cycle", "gt"]):
        grp = grp.sort_values("x_atc")
        coords = list(zip(grp.geometry.x, grp.geometry.y))
        if len(coords) < 2:
            continue
        records.append({
            "rgt":     rgt,
            "cycle":   cycle,
            "gt":      gt,
            "n_ph":    len(grp),
            "depth_mean": float(grp["ortho_h"].mean()),
            "depth_min":  float(grp["ortho_h"].min()),
            "geometry": LineString(coords),
        })
    return gpd.GeoDataFrame(records, crs="EPSG:4326")


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
def plot(points: gpd.GeoDataFrame, tracks: gpd.GeoDataFrame) -> None:
    # Reproject everything to Web Mercator for contextily
    tracks_wm = tracks.to_crs("EPSG:3857")
    aoi_wm = gpd.GeoDataFrame(geometry=[AOI_POLYGON], crs="EPSG:4326").to_crs("EPSG:3857")

    # Depth colormap
    depth_vals = tracks_wm["depth_mean"].values
    vmin, vmax = depth_vals.min(), 0.0
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.colormaps["plasma_r"]

    fig, ax = plt.subplots(figsize=(14, 10))

    # ---- Fix axes extent to AOI bounds BEFORE adding basemap ----
    bounds = aoi_wm.total_bounds          # (minx, miny, maxx, maxy) in EPSG:3857
    pad_x  = (bounds[2] - bounds[0]) * 0.05
    pad_y  = (bounds[3] - bounds[1]) * 0.05
    ax.set_xlim(bounds[0] - pad_x, bounds[2] + pad_x)
    ax.set_ylim(bounds[1] - pad_y, bounds[3] + pad_y)

    # ---- Google satellite basemap ----
    ctx.add_basemap(
        ax,
        source=GOOGLE_SAT,
        crs="EPSG:3857",
        zoom=9,
        attribution_size=8,
    )

    # ---- Track lines via LineCollection (vectorised, no extent side-effects) ----
    segments = []
    colours  = []
    for _, row in tracks_wm.iterrows():
        coords = np.array(row.geometry.coords)
        segments.append(coords)
        colours.append(cmap(norm(row["depth_mean"])))

    lc = mcoll.LineCollection(
        segments,
        colors=colours,
        linewidths=1.5,
        alpha=0.9,
        zorder=4,
    )
    ax.add_collection(lc)

    # ---- AOI polygon outline ----
    aoi_wm.boundary.plot(
        ax=ax,
        color="white",
        linewidth=2.0,
        linestyle="--",
        label="AOI",
        zorder=5,
    )

    # ---- Colourbar ----
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="vertical", pad=0.02, shrink=0.72)
    cbar.set_label("Mean seafloor depth — ortho_h (m)", fontsize=11)

    # ---- Labels & layout ----
    n_rgts = tracks_wm["rgt"].nunique()
    ax.set_title(
        f"ICESat-2 ATL24 Bathymetry — Beaufort Sea, Alaska\n"
        f"2024-07-01 → 2025-07-01  ·  {n_rgts} RGTs  ·  "
        f"{len(tracks_wm)} beam passes  ·  {len(points):,} photons",
        fontsize=13,
        pad=12,
    )
    ax.legend(loc="lower right", fontsize=10, framealpha=0.7)
    ax.set_axis_off()

    fig.tight_layout()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {OUTPUT.resolve()}")


# ---------------------------------------------------------------------------
def main() -> None:
    print(f"Loading {PARQUET} …")
    points = load(PARQUET)
    print(f"  {len(points):,} photons, {points['rgt'].nunique()} RGTs")

    print("Building track lines …")
    tracks = points_to_tracks(points)
    print(f"  {len(tracks)} beam passes")
    print(f"  Depth range: {tracks['depth_min'].min():.1f} m  →  {tracks['depth_mean'].max():.1f} m")

    print("Plotting …")
    plot(points, tracks)


if __name__ == "__main__":
    main()
