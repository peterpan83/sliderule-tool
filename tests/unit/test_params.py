"""Unit tests for parameter dataclasses."""

from __future__ import annotations

import pytest

from sliderule_tool.core.params import BaseParams
from sliderule_tool.core.region import RegionOfInterest
from sliderule_tool.datasets.arcticdem.params import ArcticDEMParams, ArcticDEMSamplingParams
from sliderule_tool.datasets.icesat2.params import (
    ATL03Params,
    ATL03xSurfaceParams,
    ATL06Params,
    ATL08Params,
    ICESat2BaseParams,
    VALID_ATL08_CLASSES,
)
from sliderule_tool.exceptions import ParameterError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _roi(n_vertices: int = 5) -> RegionOfInterest:
    """Return a RegionOfInterest backed by a synthetic polygon dict."""
    poly = [{"lon": float(i), "lat": float(i)} for i in range(n_vertices)]
    return RegionOfInterest(_raw={"poly": poly})


# ---------------------------------------------------------------------------
# BaseParams
# ---------------------------------------------------------------------------


class TestBaseParams:
    def test_to_dict_contains_poly(self):
        roi = _roi()
        p = BaseParams(region=roi)
        d = p.to_dict()
        assert "poly" in d
        assert d["poly"] == roi.poly

    def test_to_dict_no_time_keys_when_not_set(self):
        p = BaseParams(region=_roi())
        d = p.to_dict()
        assert "t0" not in d
        assert "t1" not in d

    def test_to_dict_includes_time_keys_when_set(self):
        p = BaseParams(region=_roi(), t0="2020-01-01", t1="2020-12-31")
        d = p.to_dict()
        assert d["t0"] == "2020-01-01"
        assert d["t1"] == "2020-12-31"

    def test_validate_passes_with_both_times_set(self):
        p = BaseParams(region=_roi(), t0="2020-01-01", t1="2020-12-31")
        p.validate()  # no exception

    def test_validate_passes_with_no_times(self):
        p = BaseParams(region=_roi())
        p.validate()  # no exception

    def test_validate_raises_when_only_t0_set(self):
        p = BaseParams(region=_roi(), t0="2020-01-01")
        with pytest.raises(ParameterError, match="Both t0 and t1 must be set"):
            p.validate()

    def test_validate_raises_when_only_t1_set(self):
        p = BaseParams(region=_roi(), t1="2020-12-31")
        with pytest.raises(ParameterError, match="Both t0 and t1 must be set"):
            p.validate()


# ---------------------------------------------------------------------------
# ICESat2BaseParams / ATL06Params
# ---------------------------------------------------------------------------


class TestICESat2BaseParams:
    def _make(self, **kwargs) -> ICESat2BaseParams:
        return ICESat2BaseParams(region=_roi(), **kwargs)

    def test_to_dict_has_required_icesat2_keys(self):
        p = self._make()
        d = p.to_dict()
        for key in ("res", "len", "ats", "cnt", "atl08_class", "poly"):
            assert key in d, f"Missing key: {key}"

    def test_default_values_in_dict(self):
        p = self._make()
        d = p.to_dict()
        assert d["res"] == 20.0
        assert d["len"] == 40.0
        assert d["ats"] == 10.0
        assert d["cnt"] == 10
        assert d["atl08_class"] == ["atl08_ground"]

    def test_validate_passes_for_defaults(self):
        self._make().validate()

    def test_validate_raises_on_non_positive_res(self):
        with pytest.raises(ParameterError, match="res must be positive"):
            self._make(res=0.0).validate()

    def test_validate_raises_on_non_positive_len(self):
        with pytest.raises(ParameterError, match="len must be positive"):
            self._make(len=-1.0).validate()

    def test_validate_raises_when_cnt_less_than_one(self):
        with pytest.raises(ParameterError, match="cnt must be"):
            self._make(cnt=0).validate()

    def test_validate_raises_on_invalid_atl08_class(self):
        with pytest.raises(ParameterError, match="Invalid atl08_class"):
            self._make(atl08_class=["not_a_class"]).validate()

    def test_validate_accepts_all_valid_atl08_classes(self):
        p = self._make(atl08_class=list(VALID_ATL08_CLASSES))
        p.validate()  # no exception

    def test_validate_accepts_multiple_valid_classes(self):
        p = self._make(atl08_class=["atl08_ground", "atl08_canopy"])
        p.validate()


class TestATL06Params:
    def test_is_subclass_of_icesat2_base(self):
        assert issubclass(ATL06Params, ICESat2BaseParams)

    def test_to_dict_works(self):
        p = ATL06Params(region=_roi())
        d = p.to_dict()
        assert "poly" in d and "res" in d


class TestATL03Params:
    def test_is_subclass_of_icesat2_base(self):
        assert issubclass(ATL03Params, ICESat2BaseParams)


class TestATL08Params:
    def test_is_subclass_of_icesat2_base(self):
        assert issubclass(ATL08Params, ICESat2BaseParams)


class TestATL03xSurfaceParams:
    def _make(self, **kwargs) -> ATL03xSurfaceParams:
        return ATL03xSurfaceParams(region=_roi(), **kwargs)

    def test_is_subclass_of_base_params(self):
        assert issubclass(ATL03xSurfaceParams, BaseParams)
        assert not issubclass(ATL03xSurfaceParams, ICESat2BaseParams)

    def test_to_dict_has_required_keys(self):
        d = self._make().to_dict()
        for key in ("poly", "res", "ats", "cnt", "cnf", "fit"):
            assert key in d, f"Missing key: {key}"

    def test_default_values(self):
        d = self._make().to_dict()
        assert d["res"] == 20.0
        assert d["ats"] == 10.0
        assert d["cnt"] == 10
        assert d["fit"] == {}

    def test_custom_fit_params(self):
        fit = {"maxi": 10, "H_min_win": 5.0, "sigma_r_max": 3.0}
        d = self._make(fit=fit).to_dict()
        assert d["fit"] == fit

    def test_custom_cnf(self):
        d = self._make(cnf=4).to_dict()
        assert d["cnf"] == 4

    def test_validate_passes_for_defaults(self):
        self._make().validate()

    def test_validate_raises_on_non_positive_res(self):
        with pytest.raises(ParameterError, match="res must be positive"):
            self._make(res=0.0).validate()

    def test_validate_raises_on_cnt_less_than_one(self):
        with pytest.raises(ParameterError, match="cnt must be >= 1"):
            self._make(cnt=0).validate()

    def test_validate_raises_on_non_dict_fit(self):
        with pytest.raises(ParameterError, match="fit must be a dict"):
            self._make(fit="bad").validate()


# ---------------------------------------------------------------------------
# ArcticDEMSamplingParams
# ---------------------------------------------------------------------------


class TestArcticDEMSamplingParams:
    def test_to_samples_dict_structure(self):
        sp = ArcticDEMSamplingParams(asset="arcticdem-mosaic", radius=10.0, zonal_stats=True)
        d = sp.to_samples_dict()
        assert "arcticdem-mosaic" in d
        assert d["arcticdem-mosaic"]["radius"] == 10.0
        assert d["arcticdem-mosaic"]["zonal_stats"] is True

    def test_validate_passes_for_defaults(self):
        ArcticDEMSamplingParams().validate()

    def test_validate_raises_on_invalid_asset(self):
        with pytest.raises(ParameterError, match="Invalid ArcticDEM asset"):
            ArcticDEMSamplingParams(asset="bad-asset").validate()

    def test_validate_raises_on_non_positive_radius(self):
        with pytest.raises(ParameterError, match="radius must be positive"):
            ArcticDEMSamplingParams(radius=0.0).validate()

    def test_strips_asset_accepted(self):
        sp = ArcticDEMSamplingParams(asset="arcticdem-strips")
        sp.validate()  # no exception


# ---------------------------------------------------------------------------
# ArcticDEMParams
# ---------------------------------------------------------------------------


class TestArcticDEMParams:
    def _make(self, **kwargs) -> ArcticDEMParams:
        return ArcticDEMParams(region=_roi(), **kwargs)

    def test_to_dict_includes_samples_key(self):
        p = self._make()
        d = p.to_dict()
        assert "samples" in d

    def test_samples_dict_has_arcticdem_mosaic(self):
        p = self._make()
        d = p.to_dict()
        assert "arcticdem-mosaic" in d["samples"]

    def test_samples_contains_radius(self):
        p = self._make(sampling=ArcticDEMSamplingParams(radius=25.0))
        assert p.to_dict()["samples"]["arcticdem-mosaic"]["radius"] == 25.0

    def test_validate_passes_for_defaults(self):
        self._make().validate()

    def test_validate_raises_on_bad_sampling(self):
        bad_sampling = ArcticDEMSamplingParams(asset="bogus")
        with pytest.raises(ParameterError, match="Invalid ArcticDEM asset"):
            self._make(sampling=bad_sampling).validate()

    def test_inherits_icesat2_validation(self):
        with pytest.raises(ParameterError, match="res must be positive"):
            self._make(res=-1.0).validate()

    def test_to_dict_also_has_icesat2_keys(self):
        p = self._make()
        d = p.to_dict()
        for key in ("res", "len", "ats", "cnt", "atl08_class", "poly", "samples"):
            assert key in d, f"Missing key: {key}"
