# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

All commands must run inside the `sme-chain` conda environment:

```bash
conda run -n sme-chain python ...
```

Install the package in editable mode (already done, but if needed):

```bash
conda run -n sme-chain pip install -e .
```

## Commands

```bash
# Run unit tests (no live connection required)
conda run -n sme-chain python -m pytest tests/unit/ -q

# Run a single test file
conda run -n sme-chain python -m pytest tests/unit/test_params.py -v

# Run integration tests (requires live SlideRule + NASA Earthdata credentials)
conda run -n sme-chain python -m pytest tests/integration/ -v -m integration

# Lint
conda run -n sme-chain ruff check sliderule_tool/

# Run an example script
conda run -n sme-chain python examples/arctic_atl24_download.py
```

## Architecture

### Layers (top to bottom)

```
SlideRuleTool          ← uniform façade (tool.py) — start here for all data access
    │
    ├── SlideRuleClient    core/client.py    — session lifecycle, wraps icesat2.init()
    ├── RegionOfInterest   core/region.py    — wraps sliderule.toregion(); accepts bbox/GeoJSON/shp/GDF
    ├── BaseParams         core/params.py    — to_dict() compiles typed fields → raw SlideRule parm dict
    └── AbstractDataset    core/dataset.py   — plugin base; run() = validate → fetch → write
            │
            ├── ICESat2Dataset   datasets/icesat2/dataset.py   — ATL03/06/08 via icesat2.*; ATL24 via sliderule.run("atl24x")
            └── ArcticDEMDataset datasets/arcticdem/dataset.py — ATL06 + samples dict injected by ArcticDEMParams
```

### Dataset plugin system

New datasets are added without touching existing code:
1. Create `datasets/<name>/dataset.py` — subclass `AbstractDataset`, apply `@register`
2. Create `datasets/<name>/params.py` — subclass `BaseParams` (or `ICESat2BaseParams`)
3. Add one import line in `datasets/__init__._ensure_datasets_loaded()`
4. Add the `(dataset, product)` → `ParamsClass` entry in `tool._PARAMS_MAP`

### Params compilation

Every params class is a dataclass. `to_dict()` is the single boundary between our domain and SlideRule's raw API dict. Always pass `poly` (exact polygon vertices) and `raster` (when present, for server-side efficiency) — both come from `RegionOfInterest._raw` which is the direct output of `sliderule.toregion()`.

### Key design facts

- **ArcticDEM is not standalone** — it is sampled along ICESat-2 ATL06 tracks. `ArcticDEMParams` inherits `ICESat2BaseParams` and injects a `samples` key into `to_dict()`.
- **ATL24 uses a different API call** — `sliderule.run("atl24x", parm)` instead of `icesat2.atl06p()`. Handled as a special case in `ICESat2Dataset.fetch()`.
- **Unit tests stub sliderule** — `conftest.py` at the project root installs a `sliderule` mock into `sys.modules` before any imports, so all 91 unit tests run without the real package.
- **Output format inferred from suffix** — `.parquet`, `.geojson`, `.csv` are auto-detected; `OutputWriter` creates parent directories automatically.

### Configuration

`Config` is loaded from `SLIDERULE_*` environment variables (or a `.env` file). See `.env.example` for all keys. `Config.to_sliderule_init_kwargs()` maps only the keys that `icesat2.init()` accepts.

### Output

`OutputWriter` (`output/writer.py`) dispatches to thin format handlers in `output/formats/`. CSV writes geometry as WKT. All handlers raise `OutputError` on failure.
