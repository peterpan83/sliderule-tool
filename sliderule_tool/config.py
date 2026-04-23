"""Configuration management for sliderule-tool."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration, loadable from environment variables.

    Attributes:
        api_url: SlideRule API endpoint hostname.
        organization: SlideRule organization name (optional).
        desired_nodes: Number of compute nodes to request (optional).
        timeout: Request timeout in seconds.
        max_resources: Maximum number of ICESat-2 resources to process.
        default_output_format: Default output format ('parquet', 'geojson', 'csv').
        output_dir: Directory for writing output files.
        log_level: Logging level string (e.g. 'WARNING', 'INFO', 'DEBUG').
    """

    api_url: str = "slideruleearth.io"
    organization: str | None = None
    desired_nodes: int | None = None
    timeout: int = 600
    max_resources: int = 1000
    default_output_format: str = "parquet"
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    log_level: str = "WARNING"

    @classmethod
    def load(cls, env_file: Path | None = None) -> "Config":
        """Load configuration from environment variables.

        Args:
            env_file: Optional path to a .env file. If None, attempts to load
                      a .env file from the current working directory (no error
                      if absent).

        Returns:
            A Config instance populated from the environment.
        """
        load_dotenv(env_file)  # loads .env if present, no error if absent
        return cls(
            api_url=os.getenv("SLIDERULE_API_URL", "slideruleearth.io"),
            organization=os.getenv("SLIDERULE_ORGANIZATION") or None,
            desired_nodes=(
                int(os.getenv("SLIDERULE_DESIRED_NODES"))
                if os.getenv("SLIDERULE_DESIRED_NODES")
                else None
            ),
            timeout=int(os.getenv("SLIDERULE_TIMEOUT", "600")),
            max_resources=int(os.getenv("SLIDERULE_MAX_RESOURCES", "1000")),
            default_output_format=os.getenv("SLIDERULE_DEFAULT_OUTPUT_FORMAT", "parquet"),
            output_dir=Path(os.getenv("SLIDERULE_OUTPUT_DIR", "./output")),
            log_level=os.getenv("SLIDERULE_LOG_LEVEL", "WARNING"),
        )

    def to_sliderule_init_kwargs(self) -> dict:
        """Build keyword arguments for ``icesat2.init()`` / ``sliderule.init()``.

        Returns:
            Dict containing at minimum ``loglevel``, plus optional
            ``organization`` and ``desired_nodes`` keys.
        """
        kwargs: dict = {"loglevel": getattr(logging, self.log_level, logging.WARNING)}
        if self.organization:
            kwargs["organization"] = self.organization
        if self.desired_nodes:
            kwargs["desired_nodes"] = self.desired_nodes
        return kwargs
