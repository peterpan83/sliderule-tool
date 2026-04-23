"""Exception hierarchy for sliderule-tool."""

from __future__ import annotations


class SlideRuleToolError(Exception):
    """Base exception for all sliderule-tool errors."""


class ConfigError(SlideRuleToolError):
    """Raised for configuration errors."""


class RegionError(SlideRuleToolError):
    """Raised for region-of-interest errors."""


class ParameterError(SlideRuleToolError):
    """Raised for invalid parameter values."""


class DatasetError(SlideRuleToolError):
    """Raised for dataset-related errors (unknown dataset, fetch issues)."""


class OutputError(SlideRuleToolError):
    """Raised for output writing errors."""


class APIError(SlideRuleToolError):
    """Raised when the SlideRule API returns an error or is unreachable.

    Attributes:
        original: The original exception that caused this error, if any.
    """

    def __init__(self, message: str, original: Exception | None = None) -> None:
        super().__init__(message)
        self.original = original
