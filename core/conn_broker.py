"""Minimal connection broker stubs for testing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Protocol, TypedDict


class BrokerRequest(TypedDict, total=False):
    method: str
    url: str
    query: Mapping[str, Any]
    headers: Mapping[str, str]
    timeout: float
    response_size_limit: int


class BrokerResponse(TypedDict, total=False):
    status: int
    body: Any
    headers: Mapping[str, str]


class AuthStatus(TypedDict, total=False):
    state: str  # "ready", "pending", "error"
    message: str


class BrokerHandle(Protocol):
    """Marker protocol for broker handles."""


class BrokerStream(Protocol):
    """Marker protocol for broker streams."""

    def read(self, size: int = -1) -> bytes:
        ...


class AuthorizationError(RuntimeError):
    """Raised when authorization is missing or pending."""


class BrokerInterface(Protocol):
    """Protocol representing the subset of broker behaviour needed for tests."""

    def get_auth_status(self, auth_profile: str, scopes: list[str]) -> AuthStatus:
        ...

    def get_handle(self, auth_profile: str, scopes: list[str]) -> BrokerHandle:
        ...

    def ensure_ready(self, handle: BrokerHandle, timeout: float) -> None:
        ...

    def request(self, handle: BrokerHandle, request: BrokerRequest) -> BrokerResponse:
        ...

    def stream(self, handle: BrokerHandle, request: BrokerRequest) -> BrokerStream:
        ...


