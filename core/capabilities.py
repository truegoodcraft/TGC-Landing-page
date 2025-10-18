"""Capability registry stubs."""
from __future__ import annotations

from typing import Dict, Mapping

_CAPABILITIES: Dict[str, Mapping[str, object]] = {}


def register(capability_id: str, definition: Mapping[str, object]) -> None:
    _CAPABILITIES[capability_id] = dict(definition)


def get(capability_id: str) -> Mapping[str, object]:
    return _CAPABILITIES[capability_id]


def all_capabilities() -> Mapping[str, Mapping[str, object]]:
    return dict(_CAPABILITIES)


