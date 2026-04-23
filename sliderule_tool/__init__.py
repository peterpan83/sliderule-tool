"""sliderule-tool – a high-level Python wrapper around the SlideRule Earth API."""

from sliderule_tool.config import Config
from sliderule_tool.core.client import SlideRuleClient
from sliderule_tool.core.region import RegionOfInterest
from sliderule_tool.datasets import get_dataset, list_datasets
from sliderule_tool.datasets.arcticdem.params import ArcticDEMParams, ArcticDEMSamplingParams
from sliderule_tool.datasets.icesat2.params import ATL03Params, ATL03xSurfaceParams, ATL06Params, ATL08Params, ATL24Params
from sliderule_tool.tool import SlideRuleTool

__version__ = "0.1.0"

__all__ = [
    # Uniform entry point
    "SlideRuleTool",
    # Lower-level building blocks
    "Config",
    "SlideRuleClient",
    "RegionOfInterest",
    "get_dataset",
    "list_datasets",
    "ATL03Params",
    "ATL03xSurfaceParams",
    "ATL06Params",
    "ATL08Params",
    "ATL24Params",
    "ArcticDEMParams",
    "ArcticDEMSamplingParams",
]
