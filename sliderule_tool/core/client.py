"""SlideRule session lifecycle management."""

from __future__ import annotations

import logging

from sliderule import icesat2

from sliderule_tool.config import Config
from sliderule_tool.exceptions import APIError

logger = logging.getLogger(__name__)


class SlideRuleClient:
    """Manages the SlideRule session lifecycle as a context manager.

    Example::

        config = Config.load()
        with SlideRuleClient(config) as client:
            dataset = get_dataset("icesat2", config)
            gdf = dataset.run(params)
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self._initialized = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialise the SlideRule connection.

        Idempotent: calling this on an already-initialised client is a no-op.

        Raises:
            APIError: If the ``icesat2.init()`` call fails.
        """
        if self._initialized:
            return
        kwargs = self.config.to_sliderule_init_kwargs()
        logger.info("Initializing SlideRule client at %s", self.config.api_url)
        try:
            icesat2.init(self.config.api_url, **kwargs)
            self._initialized = True
        except Exception as e:
            raise APIError(
                f"Failed to initialize SlideRule client: {e}", original=e
            ) from e

    def shutdown(self) -> None:
        """Mark the client as uninitialised (no remote teardown needed)."""
        self._initialized = False
        logger.info("SlideRule client shut down")

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> SlideRuleClient:
        self.initialize()
        return self

    def __exit__(self, *args) -> None:
        self.shutdown()
