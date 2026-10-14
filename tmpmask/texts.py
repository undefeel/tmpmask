"""Load and format localized user-facing texts."""

from __future__ import annotations

import functools
import tomllib
from pathlib import Path
from typing import Any

from tmpmask.filters import FILTER_IDS

_TEXTS_FILE = Path(__file__).resolve().parent / "texts.toml"


@functools.cache
def _load_texts() -> dict[str, Any]:
    with _TEXTS_FILE.open("rb") as f:
        return tomllib.load(f)


def t(key: str, **kwargs: Any) -> str:
    """Return formatted localized text by dot-separated key.

    Raises KeyError if key is missing or does not resolve to a string.
    """
    data: Any = _load_texts()
    parts = key.split(".")
    for part in parts:
        if not isinstance(data, dict) or part not in data:
            raise KeyError(f"No text for key: {key}")
        data = data[part]

    if not isinstance(data, str):
        raise KeyError(f"No text for key: {key}")

    return data.format(**kwargs)


def filter_name(filter_id: str) -> str:
    """Return Russian name for a filter ID."""
    if filter_id not in FILTER_IDS:
        raise KeyError(f"Unknown filter id: {filter_id!r}")
    return t(f"filters.{filter_id}")
