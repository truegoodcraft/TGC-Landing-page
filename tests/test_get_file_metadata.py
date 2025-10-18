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


def test_get_file_metadata_requests_expected_fields(fake_broker):
    handle = _build_handle(
        fake_broker,
        {
            "folder_allowlist": ["root"],
            "mime_allowlist": ["application/pdf"],
        },
    )
    fake_broker.metadata["file123"] = {
        "id": "file123",
        "parents": ["root"],
        "mimeType": "application/pdf",
    }

    metadata = files.get_file_metadata(handle, "file123")
    request = fake_broker.last_request

    assert metadata["id"] == "file123"
    assert request is not None
    assert request["query"]["fields"].startswith("id,")


def test_get_file_metadata_blocks_policy_violations(fake_broker):
    handle = _build_handle(
        fake_broker,
        {"folder_allowlist": ["root"], "mime_allowlist": ["application/pdf"]},
    )
    fake_broker.metadata["file456"] = {
        "id": "file456",
        "parents": ["not-root"],
        "mimeType": "application/vnd.ms-excel",
    }

    with pytest.raises(plugin.PolicyError):
        files.get_file_metadata(handle, "file456")


