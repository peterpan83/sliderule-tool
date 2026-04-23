"""Dataset registry and factory helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sliderule_tool.config import Config
from sliderule_tool.core.dataset import AbstractDataset
from sliderule_tool.exceptions import DatasetError

if TYPE_CHECKING:
    pass

_REGISTRY: dict[str, type[AbstractDataset]] = {}


def register(cls: type[AbstractDataset]) -> type[AbstractDataset]:
    """Class decorator that registers a dataset in the global registry.

    Args:
        cls: A concrete :class:`~sliderule_tool.core.dataset.AbstractDataset`
             subclass.  The class must define a ``name`` class variable.

    Returns:
        The class unchanged (decorator pattern).
    """
    _REGISTRY[cls.name] = cls
    return cls


def get_dataset(name: str, config: Config) -> AbstractDataset:
    """Instantiate a registered dataset by name.

    Args:
        name: The dataset identifier (e.g. ``"icesat2"``, ``"arcticdem"``).
        config: Application configuration passed to the dataset constructor.

    Returns:
        An initialised :class:`~sliderule_tool.core.dataset.AbstractDataset`
        instance.

    Raises:
        DatasetError: If ``name`` is not found in the registry.
    """
    _ensure_datasets_loaded()
    if name not in _REGISTRY:
        raise DatasetError(
            f"Unknown dataset '{name}'. Available: {list_datasets()}"
        )
    return _REGISTRY[name](config)


def list_datasets() -> list[str]:
    """Return a sorted list of all registered dataset names.

    Returns:
        Sorted list of dataset name strings.
    """
    _ensure_datasets_loaded()
    return sorted(_REGISTRY.keys())


def _ensure_datasets_loaded() -> None:
    """Lazily import dataset modules to trigger ``@register`` decorators."""
    # noqa: F401 – side-effect imports
    from sliderule_tool.datasets.icesat2 import dataset as _icesat2_ds  # noqa: F401
    from sliderule_tool.datasets.arcticdem import dataset as _arcticdem_ds  # noqa: F401
