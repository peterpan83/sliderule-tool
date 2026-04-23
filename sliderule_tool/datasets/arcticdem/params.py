"""ArcticDEM specific parameter dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field

from sliderule_tool.datasets.icesat2.params import ICESat2BaseParams
from sliderule_tool.exceptions import ParameterError

VALID_ARCTICDEM_ASSETS: frozenset[str] = frozenset(
    ["arcticdem-mosaic", "arcticdem-strips"]
)


@dataclass
class ArcticDEMSamplingParams:
    """Configuration for ArcticDEM co-sampling along ICESat-2 tracks.

    Attributes:
        asset: ArcticDEM raster asset to sample from.
        radius: Sampling radius in metres around each ICESat-2 point.
        zonal_stats: Whether to compute zonal statistics within the radius.
    """

    asset: str = "arcticdem-mosaic"
    radius: float = 10.0
    zonal_stats: bool = True

    def validate(self) -> None:
        """Validate sampling parameters.

        Raises:
            ParameterError: If ``asset`` is unrecognised or ``radius`` is not
                            positive.
        """
        if self.asset not in VALID_ARCTICDEM_ASSETS:
            raise ParameterError(
                f"Invalid ArcticDEM asset '{self.asset}'. "
                f"Valid: {VALID_ARCTICDEM_ASSETS}"
            )
        if self.radius <= 0:
            raise ParameterError(f"radius must be positive, got {self.radius}")

    def to_samples_dict(self) -> dict:
        """Serialise to the SlideRule ``samples`` sub-dict.

        Returns:
            Dict of the form ``{asset: {"radius": ..., "zonal_stats": ...}}``.
        """
        return {
            self.asset: {
                "radius": self.radius,
                "zonal_stats": self.zonal_stats,
            }
        }


@dataclass
class ArcticDEMParams(ICESat2BaseParams):
    """ICESat-2 parameters with ArcticDEM co-sampling.

    ArcticDEM elevation values are sampled at ICESat-2 track positions,
    so these parameters extend the standard ICESat-2 set with an
    :class:`ArcticDEMSamplingParams` configuration object.

    Attributes:
        sampling: Co-sampling configuration (asset, radius, zonal_stats).
    """

    sampling: ArcticDEMSamplingParams = field(
        default_factory=ArcticDEMSamplingParams
    )

    def validate(self) -> None:
        """Validate all parameters including the sampling sub-config.

        Raises:
            ParameterError: Propagated from parent or
                            :class:`ArcticDEMSamplingParams`.
        """
        super().validate()
        self.sampling.validate()

    def to_dict(self) -> dict:
        """Serialise to a SlideRule ``parm`` dict with ``samples`` key.

        Returns:
            Dict extending ICESat-2 keys with the ``samples`` entry required
            for ArcticDEM co-sampling.
        """
        d = super().to_dict()
        d["samples"] = self.sampling.to_samples_dict()
        return d
