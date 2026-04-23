# sliderule-tool

A Python tool for accessing [SlideRule Earth](https://slideruleearth.io) data products
through a single, uniform interface.

Supports ICESat-2 (ATL03, ATL03x, ATL03x-surface, ATL06, ATL08, ATL24) and
ArcticDEM elevation sampling along ICESat-2 tracks. The dataset layer is a
plugin system, so adding a new SlideRule product is a few files — no changes to
existing code.

## Install

Requires Python 3.10+.

```bash
pip install -e .
```

Set up credentials and runtime options (copy `.env.example` to `.env` and fill
in as needed):

```bash
cp .env.example .env
```

NASA Earthdata credentials are required for any actual data fetch. SlideRule
follows the standard `~/.netrc` convention.

## Quick start

```python
from sliderule_tool import SlideRuleTool

tool = SlideRuleTool()

# ICESat-2 ATL24 bathymetry from a bounding box
gdf = tool.fetch(
    dataset="icesat2",
    product="atl24",
    region=(-152.5, 70.2, -148.0, 71.3),   # (west, south, east, north)
    t0="2024-07-01",
    t1="2025-07-01",
    atl24_class=["bathymetry", "sea_surface"],
    output_path="output/bathy.parquet",
)
```

`region` accepts a bounding-box tuple, a path to a GeoJSON or shapefile, a
GeoPandas `GeoDataFrame`, or a `RegionOfInterest`. Output format is inferred
from the path suffix (`.parquet`, `.geojson`, `.csv`).

ArcticDEM is sampled along ATL06 tracks:

```python
from sliderule_tool.datasets.arcticdem.params import ArcticDEMSamplingParams

gdf = tool.fetch(
    dataset="arcticdem",
    region=(-150.0, 68.0, -148.0, 70.0),
    t0="2020-01-01",
    t1="2020-06-01",
    sampling=ArcticDEMSamplingParams(radius=15.0),
)
```

See `examples/` for runnable scripts.

## Tests

```bash
# Unit tests (no network — sliderule is stubbed in conftest.py)
python -m pytest tests/unit/ -q

# Integration tests (require live SlideRule + NASA Earthdata credentials)
python -m pytest tests/integration/ -v -m integration
```

## Architecture

```
SlideRuleTool          — uniform façade (sliderule_tool/tool.py)
    │
    ├── SlideRuleClient    session lifecycle (wraps icesat2.init)
    ├── RegionOfInterest   wraps sliderule.toregion(); bbox / GeoJSON / shp / GDF
    ├── BaseParams         dataclass → raw SlideRule parm dict
    └── AbstractDataset    plugin base; run() = validate → fetch → write
            ├── ICESat2Dataset
            └── ArcticDEMDataset
```

To add a new dataset, see the plugin notes in `CLAUDE.md`.

## License

TBD.
