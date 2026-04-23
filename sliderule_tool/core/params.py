"""Base parameter dataclass shared by all dataset parameter classes."""

from __future__ import annotations

from dataclasses import dataclass

from sliderule_tool.core.region import RegionOfInterest
from sliderule_tool.exceptions import ParameterError


@dataclass
class BaseParams:
    """Minimum set of parameters required by every SlideRule request.

    Attributes:
        region: The geographic region of interest.
        t0: Start of the temporal filter as an ISO-8601 date string
            (e.g. ``"2020-01-01"``).  Must be set together with ``t1``.
        t1: End of the temporal filter as an ISO-8601 date string.
            Must be set together with ``t0``.
    """

    region: RegionOfInterest
    t0: str | None = None  # ISO-8601 date e.g. "2020-01-01"
    t1: str | None = None

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Validate region and temporal consistency.

        Raises:
            RegionError: Propagated from :meth:`RegionOfInterest.validate`.
            ParameterError: If only one of ``t0`` / ``t1`` is set.
        """
        self.region.validate()
        if (self.t0 is None) != (self.t1 is None):
            raise ParameterError("Both t0 and t1 must be set, or neither")

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise parameters to a ``parm`` dict accepted by the SlideRule API.

        Always includes ``poly`` (the exact polygon vertices).  When the region
        also carries a ``raster`` entry — produced by ``sliderule.toregion()``
        for complex polygons — it is included too so SlideRule can use
        rasterized filtering instead of per-vertex intersection, which is
        significantly faster for polygons with many vertices.

        Returns:
            Dict with at minimum the ``poly`` key, plus optional ``raster``,
            ``t0``, and ``t1``.
        """
        d: dict = {"poly": self.region.poly}
        if self.region.raster is not None:
            d["raster"] = self.region.raster
        if self.t0:
            d["t0"] = self.t0
        if self.t1:
            d["t1"] = self.t1
        return d
