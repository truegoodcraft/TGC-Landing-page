"""Minimal secrets/settings stubs."""
from __future__ import annotations

from typing import Any, Dict

_SETTINGS: dict[str, Dict[str, Any]] = {}


def set_settings(plugin_id: str, settings: Dict[str, Any]) -> None:
    _SETTINGS[plugin_id] = dict(settings)


def get_settings(plugin_id: str) -> Dict[str, Any]:
    return dict(_SETTINGS.get(plugin_id, {}))


def clear_settings() -> None:
    _SETTINGS.clear()


