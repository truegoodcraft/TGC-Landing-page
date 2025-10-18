from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import secrets
from core.conn_broker import AuthorizationError, BrokerRequest, BrokerResponse


@dataclass
class FakeBrokerHandle:
    token: str = "handle"


@dataclass
class FakeStream:
    chunks: List[bytes] = field(default_factory=list)

    def read(self, size: int = -1) -> bytes:
        if not self.chunks:
            return b""
        return self.chunks.pop(0)


class FakeBroker:
    def __init__(self):
        self.auth_status: Dict[str, Dict[str, str]] = {}
        self.last_request: Optional[BrokerRequest] = None
        self.last_stream_request: Optional[BrokerRequest] = None
        self.ensure_ready_called = False
        self.stream_response: FakeStream = FakeStream()
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def get_auth_status(self, auth_profile: str, scopes: list[str]):
        return self.auth_status.get(auth_profile, {"state": "pending"})

    def get_handle(self, auth_profile: str, scopes: list[str]):
        status = self.get_auth_status(auth_profile, scopes)
        if status.get("state") != "ready":
            raise AuthorizationError("authorization pending")
        return FakeBrokerHandle(token=f"{auth_profile}:token")

    def ensure_ready(self, handle, timeout: float) -> None:
        if not isinstance(handle, FakeBrokerHandle):
            raise TypeError("Unexpected handle type")
        if not handle.token:
            raise AuthorizationError("missing token")
        self.ensure_ready_called = True

    def request(self, handle, request: BrokerRequest) -> BrokerResponse:
        self.last_request = request
        if not isinstance(handle, FakeBrokerHandle):
            raise TypeError("Unexpected handle type")
        if request["method"] == "GET" and request["url"].endswith("alt=media"):
            raise AssertionError("metadata path should not include alt=media")
        if "fields" in request.get("query", {}):
            file_id = request["url"].split("/")[-1]
            if file_id in self.metadata:
                return {"status": 200, "body": self.metadata[file_id]}
        return {"status": 200, "body": {}}

    def stream(self, handle, request: BrokerRequest):
        self.last_stream_request = request
        return self.stream_response


@pytest.fixture(autouse=True)
def reset_state():
    secrets.clear_settings()
    import plugins.google_drive_read.plugin as plugin_module

    plugin_module._broker = None
    yield


@pytest.fixture
def fake_broker():
    return FakeBroker()


