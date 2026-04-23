"""Uniform entry point for the SlideRule tool.

All dataset access can be performed through a single :class:`SlideRuleTool`
instance, without manually managing ``Config``, ``SlideRuleClient``, or
``RegionOfInterest`` objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import geopandas as gpd

from sliderule_tool.config import Config
from sliderule_tool.core.client import SlideRuleClient
from sliderule_tool.core.region import RegionOfInterest
from sliderule_tool.datasets import get_dataset
from sliderule_tool.datasets.arcticdem.params import ArcticDEMParams, ArcticDEMSamplingParams
from sliderule_tool.datasets.icesat2.params import (
    ATL03Params,
    ATL03xParams,
    ATL03xSurfaceParams,
    ATL06Params,
    ATL08Params,
    ATL24Params,
    ICESat2BaseParams,
)
from sliderule_tool.exceptions import ParameterError

# Type alias for the region argument accepted by fetch()
RegionInput = Union[
    RegionOfInterest,       # already constructed
    str,                    # path to GeoJSON or shapefile
    Path,                   # path to GeoJSON or shapefile
    gpd.GeoDataFrame,       # GeoPandas GeoDataFrame
    tuple,                  # (west, south, east, north) bounding box
]

# Maps (dataset, product) → params class
_PARAMS_MAP: dict[tuple[str, str], type] = {
    ("icesat2", "atl03"): ATL03Params,
    ("icesat2", "atl03x"): ATL03xParams,
    ("icesat2", "atl03x-surface"): ATL03xSurfaceParams,
    ("icesat2", "atl06"): ATL06Params,
    ("icesat2", "atl08"): ATL08Params,
    ("icesat2", "atl24"): ATL24Params,
    ("arcticdem", "atl06"): ArcticDEMParams,
}


def _resolve_region(region: RegionInput) -> RegionOfInterest:
    if isinstance(region, RegionOfInterest):
        return region
    if isinstance(region, gpd.GeoDataFrame):
        return RegionOfInterest.from_geodataframe(region)
    if isinstance(region, tuple):
        if len(region) != 4:
            raise ParameterError("Bounding box tuple must be (west, south, east, north)")
        return RegionOfInterest.from_bbox(*region)
    path = str(region)
    if path.endswith(".shp"):
        return RegionOfInterest.from_shapefile(path)
    return RegionOfInterest.from_geojson(path)


class SlideRuleTool:
    """Uniform entry point for all SlideRule data access.

    Wraps ``Config``, ``SlideRuleClient``, and dataset selection behind a
    single, reusable object.  The client session is initialised on first use
    and reused across calls.

    Parameters
    ----------
    config:
        Optional :class:`~sliderule_tool.config.Config` instance.  When
        omitted, ``Config.load()`` is called (reads ``SLIDERULE_*`` env vars
        and any ``.env`` file).

    Examples
    --------
    ICESat-2 ATL24 bathymetry from a GeoJSON file::

        tool = SlideRuleTool()
        gdf = tool.fetch(
            dataset="icesat2",
            product="atl24",
            region="study_area.geojson",
            t0="2022-01-01",
            t1="2022-12-31",
            output_path="output/bathy.parquet",
        )

    ArcticDEM co-sampling from a bounding box::

        tool = SlideRuleTool()
        gdf = tool.fetch(
            dataset="arcticdem",
            region=(-150.0, 68.0, -148.0, 70.0),
            t0="2020-01-01",
            t1="2020-06-01",
            sampling=ArcticDEMSamplingParams(radius=15.0),
        )
    """

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.load()
        self._client: SlideRuleClient | None = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def open(self) -> "SlideRuleTool":
        """Initialise the SlideRule session explicitly. Returns ``self``."""
        if self._client is None:
            self._client = SlideRuleClient(self.config)
            self._client.initialize()
        return self

    def close(self) -> None:
        """Shut down the SlideRule session."""
        if self._client is not None:
            self._client.shutdown()
            self._client = None

    def __enter__(self) -> "SlideRuleTool":
        return self.open()

    def __exit__(self, *args) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def fetch(
        self,
        dataset: str,
        region: RegionInput,
        *,
        product: str | None = None,
        t0: str | None = None,
        t1: str | None = None,
        output_path: str | Path | None = None,
        output_format: str | None = None,
        **params_kwargs,
    ) -> gpd.GeoDataFrame:
        """Fetch data from any SlideRule dataset.

        Parameters
        ----------
        dataset:
            Dataset name: ``'icesat2'`` or ``'arcticdem'``.
        region:
            Area of interest — one of:

            - :class:`~sliderule_tool.core.region.RegionOfInterest`
            - Path to a GeoJSON or shapefile (``str`` or :class:`pathlib.Path`)
            - ``(west, south, east, north)`` bounding box tuple
            - :class:`geopandas.GeoDataFrame`

        product:
            ICESat-2 product variant: ``'atl03'``, ``'atl03x'``,
            ``'atl03x-surface'``, ``'atl06'``, ``'atl08'``, ``'atl24'``.
            Defaults to ``'atl06'`` for ``icesat2`` and ``'atl06'`` for
            ``arcticdem``.  Use ``'atl03x'`` for extended per-photon data
            with absolute x_atc.  Use ``'atl03x-surface'`` for per-photon
            data with ATL06-SR surface fitting (h_mean, dh_fit_dx, etc.).
        t0:
            Start date (ISO-8601, e.g. ``'2022-01-01'``).
        t1:
            End date (ISO-8601, e.g. ``'2022-12-31'``).
        output_path:
            If provided, save the result to this path.
        output_format:
            Output format (``'parquet'``, ``'geojson'``, ``'csv'``).
            Inferred from ``output_path`` suffix when omitted.
        **params_kwargs:
            Additional keyword arguments forwarded to the params dataclass
            constructor (e.g. ``res=20.0``, ``atl24_class=['bathymetry']``,
            ``sampling=ArcticDEMSamplingParams(radius=15.0)``).

        Returns
        -------
        geopandas.GeoDataFrame
        """
        # Auto-initialise session if not already open
        if self._client is None:
            self.open()

        # Resolve product default
        dataset_key = dataset.lower()
        product_key = (product or _default_product(dataset_key)).lower()

        # Build region
        roi = _resolve_region(region)

        # Build params
        params = _build_params(dataset_key, product_key, roi, t0, t1, **params_kwargs)

        # Infer output format from path suffix when not given explicitly
        fmt = output_format or _infer_format(output_path)

        # Fetch
        ds = get_dataset(dataset_key, self.config)
        return ds.run(
            params,
            product=product_key,
            output_path=Path(output_path) if output_path else None,
            output_format=fmt,
        )


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _default_product(dataset: str) -> str:
    defaults = {"icesat2": "atl06", "arcticdem": "atl06"}
    return defaults.get(dataset, "atl06")


def _build_params(
    dataset: str,
    product: str,
    region: RegionOfInterest,
    t0: str | None,
    t1: str | None,
    **kwargs,
) -> object:
    key = (dataset, product)
    cls = _PARAMS_MAP.get(key)
    if cls is None:
        available = [f"{d}/{p}" for d, p in _PARAMS_MAP]
        raise ParameterError(
            f"Unknown dataset/product '{dataset}/{product}'. "
            f"Available: {available}"
        )
    return cls(region=region, t0=t0, t1=t1, **kwargs)


def _infer_format(path: str | Path | None) -> str | None:
    if path is None:
        return None
    suffix = Path(path).suffix.lower()
    return {".parquet": "parquet", ".geojson": "geojson", ".csv": "csv"}.get(suffix)
