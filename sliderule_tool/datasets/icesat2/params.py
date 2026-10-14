"""ICESat-2 specific parameter dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field

from sliderule_tool.core.params import BaseParams
from sliderule_tool.exceptions import ParameterError

VALID_ATL24_CLASSES: frozenset[str] = frozenset(
    ["bathymetry", "sea_surface", "unclassified"]
)

VALID_ATL08_CLASSES: frozenset[str] = frozenset(
    [
        "atl08_noise",
        "atl08_ground",
        "atl08_canopy",
        "atl08_top_of_canopy",
        "atl08_unclassified",
    ]
)


@dataclass
class ICESat2BaseParams(BaseParams):
    """Common ICESat-2 request parameters shared by ATL03/06/08.

    Attributes:
        res: Along-track resolution in metres.
        len: Segment length in metres.
        ats: Minimum along-track spread in metres.
        cnt: Minimum photon count per segment.
        atl08_class: List of ATL08 surface classifications to include.
    """

    res: float = 20.0           # along-track resolution (metres)
    len: float = 40.0           # segment length (metres)
    ats: float = 10.0           # minimum along-track spread
    cnt: int = 10               # minimum photon count per segment
    atl08_class: list[str] = field(default_factory=lambda: ["atl08_ground"])

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Validate all ICESat-2 parameters.

        Raises:
            ParameterError: If any value is out of range or invalid.
            RegionError: Propagated from :class:`BaseParams`.
        """
        super().validate()
        if self.res <= 0:
            raise ParameterError(f"res must be positive, got {self.res}")
        if self.len <= 0:
            raise ParameterError(f"len must be positive, got {self.len}")
        if self.cnt < 1:
            raise ParameterError(f"cnt must be >= 1, got {self.cnt}")
        invalid = set(self.atl08_class) - VALID_ATL08_CLASSES
        if invalid:
            raise ParameterError(
                f"Invalid atl08_class values: {invalid}. Valid: {VALID_ATL08_CLASSES}"
            )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a SlideRule ``parm`` dict.

        Returns:
            Dict extending the base ``poly``/``t0``/``t1`` keys with
            ICESat-2 specific keys.
        """
        d = super().to_dict()
        d.update(
            {
                "res": self.res,
                "len": self.len,
                "ats": self.ats,
                "cnt": self.cnt,
                "atl08_class": self.atl08_class,
            }
        )
        return d


@dataclass
class ATL03Params(ICESat2BaseParams):
    """Parameters for ATL03 photon-level data subsetting via atl03sp."""


@dataclass
class ATL03xParams(BaseParams):
    """Parameters for ATL03x extended per-photon data via sliderule.run('atl03x').

    ATL03x returns raw per-photon data with absolute x_atc coordinates.
    Unlike atl03sp, it does not use segment processing parameters (res, len,
    ats, cnt) or atl08_class filtering.
    """


@dataclass
class ATL03xSurfaceParams(BaseParams):
    """Parameters for ATL03x with ATL06-SR surface fitting via sliderule.run('atl03x').

    Combines per-photon ATL03x data with the ATL06-SR surface fitting
    algorithm.  Including ``fit`` (even as an empty dict) enables the
    iterative line-segment fit that produces ``h_mean``, ``dh_fit_dx``,
    ``w_surface_window_final``, etc.

    Attributes:
        res: Along-track resolution in metres.
        ats: Minimum along-track spread in metres.
        cnt: Minimum photon count per segment.
        cnf: Photon confidence level filter (e.g. ``icesat2.CNF_SURFACE_HIGH``
             or a list such as ``['atl03_high']``).
        fit: ATL06-SR fit parameters.  Pass ``{}`` for server defaults, or
             supply ``{'maxi': …, 'H_min_win': …, 'sigma_r_max': …}``.
    """

    res: float = 20.0
    ats: float = 10.0
    cnt: int = 10
    cnf: object = field(default_factory=lambda: ["atl03_high"])
    fit: dict = field(default_factory=dict)

    def validate(self) -> None:
        super().validate()
        if self.res <= 0:
            raise ParameterError(f"res must be positive, got {self.res}")
        if self.cnt < 1:
            raise ParameterError(f"cnt must be >= 1, got {self.cnt}")
        if not isinstance(self.fit, dict):
            raise ParameterError(f"fit must be a dict, got {type(self.fit).__name__}")

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "res": self.res,
                "ats": self.ats,
                "cnt": self.cnt,
                "cnf": self.cnf,
                "fit": self.fit,
            }
        )
        return d


@dataclass
class ATL06Params(ICESat2BaseParams):
    """Parameters for ATL06-SR land-ice elevation processing."""


@dataclass
class ATL08Params(ICESat2BaseParams):
    """Parameters for ATL08 vegetation / canopy classification."""


@dataclass
class ATL24Params(BaseParams):
    """Parameters for ATL24 coastal and nearshore bathymetry.

    ATL24 uses a separate processing pipeline (``atl24x``) and requires
    ``srt=-1`` and ``cnf=-1`` to pass all photons through for bathymetry
    classification. Unlike the land-ice products, it does NOT use
    ``ICESat2BaseParams`` because ``atl08_class`` filtering is not applicable.

    Attributes:
        len: Along-track extent length in metres.
        res: Distance between subsequent extent centres in metres.
        srt: Surface type (-1 = dynamic, passes all photons; required for ATL24).
        cnf: Confidence level (-1 = no native filtering; required for ATL24).
        atl24_class: Photon classifications to include.
    """

    len: float = 40.0
    res: float = 20.0
    srt: int = -1   # dynamic — required to allow all ATL24 photons
    cnf: int = -1   # no native filtering — required for ATL24
    atl24_class: list[str] = field(default_factory=lambda: ["bathymetry", "sea_surface"])

    def validate(self) -> None:
        super().validate()
        if self.len <= 0:
            raise ParameterError(f"len must be positive, got {self.len}")
        if self.res <= 0:
            raise ParameterError(f"res must be positive, got {self.res}")
        invalid = set(self.atl24_class) - VALID_ATL24_CLASSES
        if invalid:
            raise ParameterError(
                f"Invalid atl24_class values: {invalid}. Valid: {VALID_ATL24_CLASSES}"
            )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "len": self.len,
                "res": self.res,
                "srt": self.srt,
                "cnf": self.cnf,
                # The atl24x endpoint reads the class filter from atl24.class_ph;
                # a top-level "atl24_class" key is silently ignored (server then
                # returns only its default class, bathymetry).
                "atl24": {"class_ph": list(self.atl24_class)},
            }
        )
        return d
