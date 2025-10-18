from __future__ import annotations

import pytest

from core import secrets

from plugins.google_drive_read import plugin
from plugins.google_drive_read.services import files


def _build_handle(fake_broker, settings=None):
    secrets.set_settings("google_drive_read", settings or {})
    fake_broker.auth_status["bus:google"] = {"state": "ready"}
    provider = plugin.register_broker(fake_broker)
    return provider.build_handle()


def test_stream_file_returns_broker_stream(fake_broker):
    handle = _build_handle(
        fake_broker,
        {
            "folder_allowlist": ["root"],
            "mime_allowlist": ["application/pdf"],
        },
    )
    fake_broker.metadata["file789"] = {
        "id": "file789",
        "parents": ["root"],
        "mimeType": "application/pdf",
    }
    fake_broker.stream_response.chunks = [b"chunk1", b"chunk2"]

    stream = files.stream_file(handle, "file789")
    request = fake_broker.last_stream_request

    assert stream.read() == b"chunk1"
    assert request is not None
    assert request["query"]["alt"] == "media"
    assert request["url"].endswith("file789")


def test_stream_file_blocks_policy(fake_broker):
    handle = _build_handle(
        fake_broker,
        {"folder_allowlist": ["root"]},
    )
    fake_broker.metadata["badfile"] = {
        "id": "badfile",
        "parents": ["restricted"],
        "mimeType": "application/pdf",
    }

    with pytest.raises(plugin.PolicyError):
        files.stream_file(handle, "badfile")


