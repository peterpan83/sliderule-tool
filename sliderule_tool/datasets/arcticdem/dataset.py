"""ArcticDEM dataset implementation (elevation sampled along ICESat-2 tracks)."""

from __future__ import annotations

import logging

import geopandas as gpd
from sliderule import icesat2

from sliderule_tool.core.dataset import AbstractDataset
from sliderule_tool.core.params import BaseParams
from sliderule_tool.datasets import register
from sliderule_tool.exceptions import APIError

logger = logging.getLogger(__name__)


@register
class ArcticDEMDataset(AbstractDataset):
    """ArcticDEM elevation sampled along ICESat-2 tracks.

    Uses ``icesat2.atl06p()`` with a ``samples`` dict in the parameter
    object to request ArcticDEM co-sampling.  The ``params`` object is
    expected to be an :class:`~sliderule_tool.datasets.arcticdem.params.ArcticDEMParams`
    instance whose :meth:`to_dict` method produces the required
    ``samples`` key automatically.
    """

    name = "arcticdem"
    description = "ArcticDEM elevation sampled along ICESat-2 tracks"

    def fetch(self, params: BaseParams, **kwargs) -> gpd.GeoDataFrame:
        """Fetch ArcticDEM-sampled ICESat-2 elevation data.

        Args:
            params: Request parameters; should be an
                    :class:`~sliderule_tool.datasets.arcticdem.params.ArcticDEMParams`
                    instance so that ``to_dict()`` includes the ``samples`` key.
            **kwargs: Ignored (accepted for API consistency).

        Returns:
            GeoDataFrame with ICESat-2 elevation and co-sampled ArcticDEM
            columns.

        Raises:
            APIError: If the SlideRule API call fails.
        """
        parm = params.to_dict()
        logger.debug("ArcticDEM request with parm: %s", parm)
        try:
            gdf = icesat2.atl06p(parm, asset="icesat2")
        except Exception as e:
            raise APIError(
                f"ArcticDEM sampling request failed: {e}", original=e
            ) from e
        if gdf is None or len(gdf) == 0:
            logger.warning("ArcticDEM request returned no data")
            return gpd.GeoDataFrame()
        return gdf
