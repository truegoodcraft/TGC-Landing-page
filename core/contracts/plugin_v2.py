"""Minimal stubs for Core plugin v2 contracts used in tests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, TypedDict


class PluginStatus(TypedDict, total=False):
    state: str
    message: str


class PluginDescription(TypedDict, total=False):
    id: str
    version: str
    ready: bool
    provides: List[str]
    services: List[str]
    status: PluginStatus


class BrokerProvider(Protocol):
    """Protocol representing a broker provider factory."""

    def build_handle(self) -> Any:
        ...


class ProbeResult(TypedDict, total=False):
    status: str
    latency_ms: float
    reason: str


@dataclass
class PluginRegistration:
    provider: BrokerProvider
    probe: Any


