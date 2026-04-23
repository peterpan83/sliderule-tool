"""ICESat-2 dataset implementation (ATL03/06/08 products)."""

from __future__ import annotations

import logging

import geopandas as gpd
import sliderule
from sliderule import icesat2

from sliderule_tool.core.dataset import AbstractDataset
from sliderule_tool.core.params import BaseParams
from sliderule_tool.datasets import register
from sliderule_tool.exceptions import APIError, ParameterError

logger = logging.getLogger(__name__)


@register
class ICESat2Dataset(AbstractDataset):
    """ICESat-2 photon and land-ice elevation products (ATL03/06/08).

    Supported products
    ------------------
    atl03
        Photon-level data subsetting via ``icesat2.atl03sp()``.
    atl06
        Land-ice elevation processing via ``icesat2.atl06p()``.
    atl08
        Vegetation / canopy classification via ``icesat2.atl08p()``.
    """

    name = "icesat2"
    description = "ICESat-2 photon and land-ice elevation products (ATL03/06/08/24)"

    # Standard products: called as fn(parm, asset="icesat2")
    _PRODUCT_MAP: dict = {
        "atl03": icesat2.atl03sp,
        "atl06": icesat2.atl06p,
        "atl08": icesat2.atl08p,
    }

    def fetch(
        self,
        params: BaseParams,
        product: str = "atl06",
        **kwargs,
    ) -> gpd.GeoDataFrame:
        """Fetch ICESat-2 data from the SlideRule API.

        Args:
            params: Request parameters with region and processing options.
            product: Product identifier – one of ``'atl03'``, ``'atl06'``,
                     ``'atl08'``, ``'atl24'``.
            **kwargs: Ignored (accepted for API consistency).

        Returns:
            GeoDataFrame with retrieved data.

        Raises:
            ParameterError: If ``product`` is not recognised.
            APIError: If the SlideRule API call fails.
        """
        product_key = product.lower()
        parm = params.to_dict()
        logger.debug("ICESat-2 %s request with parm: %s", product_key, parm)

        try:
            if product_key == "atl24":
                # ATL24 uses the generic sliderule.run() entry point
                gdf = sliderule.run("atl24x", parm)
            elif product_key in ("atl03x", "atl03x-surface"):
                # ATL03x endpoints: both use sliderule.run("atl03x", parm).
                # atl03x-surface includes fit/res/ats/cnt params for surface fitting.
                gdf = sliderule.run("atl03x", parm)
            else:
                fn = self._PRODUCT_MAP.get(product_key)
                if fn is None:
                    raise ParameterError(
                        f"Unknown ICESat-2 product '{product}'. "
                        f"Available: {list(self._PRODUCT_MAP) + ['atl24', 'atl03x', 'atl03x-surface']}"
                    )
                gdf = fn(parm)
        except ParameterError:
            raise
        except Exception as e:
            raise APIError(
                f"ICESat-2 {product} request failed: {e}", original=e
            ) from e

        if gdf is None or len(gdf) == 0:
            logger.warning("ICESat-2 %s returned no data", product_key)
            return gpd.GeoDataFrame()
        return gdf
