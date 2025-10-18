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


def test_list_files_enforces_folder_allowlist(fake_broker):
    handle = _build_handle(
        fake_broker,
        {"folder_allowlist": ["allowed"]},
    )
    with pytest.raises(plugin.PolicyError):
        files.list_files(handle, {"folder_id": "not-allowed"})


def test_list_files_capped_page_size_and_query(fake_broker):
    handle = _build_handle(
        fake_broker,
        {
            "folder_allowlist": ["root"],
            "mime_allowlist": ["application/pdf"],
            "max_page_size": 120,
        },
    )
    result = files.list_files(
        handle,
        {
            "folder_id": "root",
            "mime_types": ["application/pdf"],
            "owners": ["alice@example.com"],
            "name_contains": "Q1",
            "page_size": 500,
            "order_by": "modifiedTime desc",
            "page_token": "token123",
        },
    )

    request = fake_broker.last_request
    assert request is not None
    assert request["query"]["pageSize"] == "120"
    assert "token123" == request["query"]["pageToken"]
    assert request["query"]["orderBy"] == "modifiedTime desc"
    assert "mimeType" in request["query"]["q"]
    assert result == {}


