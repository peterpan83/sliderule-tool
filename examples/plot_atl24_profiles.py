"""Plot ICESat-2 ATL24 bathymetry depth profiles for every track.

One subplot per RGT.  Within each subplot the 6 ICESat-2 beams (gt) are
drawn as individual coloured lines, with depth (ortho_h) on the Y-axis and
latitude on the X-axis.

Run:
    python examples/plot_atl24_profiles.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
PARQUET = Path(__file__).parent.parent / "output" / "arctic_beaufort_atl24.parquet"
OUTPUT  = Path(__file__).parent.parent / "output" / "arctic_beaufort_atl24_profiles.png"

# ICESat-2 beam labels and colours (gt → label/colour)
GT_META: dict[int, dict] = {
    10: {"label": "GT1L", "color": "#e41a1c"},   # strong
    20: {"label": "GT1R", "color": "#ff7f7f"},   # weak
    30: {"label": "GT2L", "color": "#377eb8"},   # strong
    40: {"label": "GT2R", "color": "#7fbfff"},   # weak
    50: {"label": "GT3L", "color": "#4daf4a"},   # strong
    60: {"label": "GT3R", "color": "#a8d5a2"},   # weak
}

MIN_POINTS = 5   # skip beam passes with fewer photons than this


# ---------------------------------------------------------------------------
def load(path: Path) -> pd.DataFrame:
    gdf = gpd.read_parquet(path).set_crs("EPSG:4326", allow_override=True)
    df = pd.DataFrame(gdf.drop(columns="geometry"))
    df["lat"] = gdf.geometry.y
    df["lon"] = gdf.geometry.x
    return df


def make_grid(df: pd.DataFrame) -> tuple[list[int], int, int]:
    """Return sorted RGT list and grid dimensions (ncols, nrows)."""
    rgts = sorted(df["rgt"].unique())
    ncols = 3
    nrows = math.ceil(len(rgts) / ncols)
    return rgts, ncols, nrows


# ---------------------------------------------------------------------------
def plot(df: pd.DataFrame) -> None:
    rgts, ncols, nrows = make_grid(df)

    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(ncols * 6.5, nrows * 3.5),
        sharey=True,
        constrained_layout=True,
    )
    axes_flat = axes.flatten()

    # Global y limits (add 5 % padding)
    y_min = df["ortho_h"].min()
    y_max = df["ortho_h"].max()
    y_pad = (y_max - y_min) * 0.05

    for idx, rgt in enumerate(rgts):
        ax = axes_flat[idx]
        sub = df[df["rgt"] == rgt]
        cycles = sub["cycle"].unique()

        legend_handles = []
        for gt, meta in GT_META.items():
            for cycle in cycles:
                beam = sub[(sub["gt"] == gt) & (sub["cycle"] == cycle)].copy()
                if len(beam) < MIN_POINTS:
                    continue
                beam = beam.sort_values("x_atc")

                # Distance from the first photon of this beam pass (metres)
                dist_m = beam["x_atc"] - beam["x_atc"].iloc[0]

                sc = ax.scatter(
                    dist_m,
                    beam["ortho_h"],
                    color=meta["color"],
                    s=2,
                    linewidths=0,
                    alpha=0.7,
                    label=meta["label"],
                    zorder=3,
                )
                legend_handles.append((meta["label"], meta["color"]))

        # Sea-surface reference line
        ax.axhline(0, color="deepskyblue", linewidth=0.8, linestyle="--",
                   alpha=0.8, zorder=2, label="Sea surface")

        ax.set_ylim(y_min - y_pad, y_max + y_pad)
        ax.set_title(f"RGT {rgt}", fontsize=11, fontweight="bold", pad=4)
        ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k" if x >= 1000 else f"{x:.0f}")
        )
        ax.tick_params(labelsize=9)
        ax.grid(linestyle=":", linewidth=0.5, alpha=0.5)

        # X-axis label only on bottom row
        if idx >= (nrows - 1) * ncols:
            ax.set_xlabel("Along-track distance from start (m)", fontsize=10)

        # Y-axis label only on left column
        if idx % ncols == 0:
            ax.set_ylabel("Depth  ortho_h (m)", fontsize=10)

    # Shared proxy legend in the first visible axes
    import matplotlib.lines as mlines
    import matplotlib.patches as mpatches
    proxy_handles = [
        mlines.Line2D([], [], color=meta["color"], marker="o", markersize=4,
                      linestyle="None", label=meta["label"])
        for meta in GT_META.values()
    ] + [
        mlines.Line2D([], [], color="deepskyblue", linewidth=1.2,
                      linestyle="--", label="Sea surface (0 m)")
    ]
    axes_flat[0].legend(
        handles=proxy_handles,
        fontsize=9, ncol=2,
        loc="lower right",
        framealpha=0.85,
        title="Beam / Reference",
        title_fontsize=9,
    )

    # Hide unused subplots
    for j in range(len(rgts), len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle(
        "ICESat-2 ATL24 Bathymetry Profiles — Beaufort Sea, Alaska\n"
        "2024-07-01 → 2025-07-01  ·  depth vs along-track distance per RGT",
        fontsize=13,
        y=1.01,
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {OUTPUT.resolve()}")


# ---------------------------------------------------------------------------
def main() -> None:
    print(f"Loading {PARQUET} …")
    df = load(PARQUET)
    print(f"  {len(df):,} photons · {df['rgt'].nunique()} RGTs · "
          f"{len(df.groupby(['rgt','cycle','gt']))} beam passes")
    print("Plotting profiles …")
    plot(df)


if __name__ == "__main__":
    main()
