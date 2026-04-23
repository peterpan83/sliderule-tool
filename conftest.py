"""Root conftest.py: install a lightweight ``sliderule`` mock into sys.modules
before any sliderule_tool code is imported.

This allows the entire unit-test suite to run without the real ``sliderule``
package being installed.  Integration tests that need a live connection should
be run separately once ``sliderule`` is installed (``pip install sliderule``).
"""

from __future__ import annotations

import sys
import types
import unittest.mock as mock


def _install_sliderule_mock() -> None:
    """Create stub ``sliderule`` and ``sliderule.icesat2`` modules."""
    if "sliderule" in sys.modules:
        return  # already installed (real or mock)

    sr = types.ModuleType("sliderule")
    sr.toregion = mock.MagicMock(
        return_value={
            "poly": [
                {"lon": -150.5, "lat": 69.0},
                {"lon": -148.5, "lat": 69.0},
                {"lon": -148.5, "lat": 70.0},
                {"lon": -150.5, "lat": 70.0},
                {"lon": -150.5, "lat": 69.0},
            ],
            "raster": {},
        }
    )
    sr.init = mock.MagicMock()
    sr.run = mock.MagicMock(return_value=None)

    icesat2 = types.ModuleType("sliderule.icesat2")
    icesat2.init = mock.MagicMock()
    icesat2.atl03sp = mock.MagicMock(return_value=None)
    icesat2.atl06p = mock.MagicMock(return_value=None)
    icesat2.atl08p = mock.MagicMock(return_value=None)

    sr.icesat2 = icesat2
    sys.modules["sliderule"] = sr
    sys.modules["sliderule.icesat2"] = icesat2


_install_sliderule_mock()
