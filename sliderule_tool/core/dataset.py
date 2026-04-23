"""Abstract base class for all dataset implementations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

import geopandas as gpd

from sliderule_tool.config import Config
from sliderule_tool.core.params import BaseParams

logger = logging.getLogger(__name__)


class AbstractDataset(ABC):
    """Base class every concrete dataset must subclass.

    Subclasses must define class variables ``name`` and ``description``,
    and implement the :meth:`fetch` method.

    Attributes:
        name: Short identifier used to look up the dataset in the registry.
        description: Human-readable description of the dataset.
    """

    name: ClassVar[str]
    description: ClassVar[str]

    def __init__(self, config: Config) -> None:
        self.config = config

    @abstractmethod
    def fetch(self, params: BaseParams, **kwargs) -> gpd.GeoDataFrame:
        """Fetch data from the SlideRule API.

        Args:
            params: Request parameters (region, time range, product options).
            **kwargs: Additional dataset-specific keyword arguments.

        Returns:
            A GeoDataFrame containing the retrieved data.
        """
        ...

    def run(
        self,
        params: BaseParams,
        output_path: Path | None = None,
        output_format: str | None = None,
        **kwargs,
    ) -> gpd.GeoDataFrame:
        """Validate parameters, fetch data, and optionally write output.

        Args:
            params: Request parameters; :meth:`BaseParams.validate` is called
                    before the API request.
            output_path: If provided, write results to this path.
            output_format: Output format override (``'parquet'``, ``'geojson'``,
                           ``'csv'``).  Falls back to
                           :attr:`Config.default_output_format`.
            **kwargs: Forwarded to :meth:`fetch`.

        Returns:
            The fetched GeoDataFrame (also written to disk if requested).
        """
        params.validate()
        logger.info("Fetching data from dataset '%s'", self.name)
        gdf = self.fetch(params, **kwargs)
        logger.info("Received %d records", len(gdf))

        if output_path is not None or output_format is not None:
            from sliderule_tool.output.writer import OutputWriter

            writer = OutputWriter(self.config)
            saved_path = writer.write(gdf, output_path, output_format)
            logger.info("Saved output to %s", saved_path)

        return gdf
