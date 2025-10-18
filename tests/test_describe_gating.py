from __future__ import annotations

from core import secrets

from plugins.google_drive_read import plugin


def test_describe_pending_without_auth(fake_broker):
    plugin.register_broker(fake_broker)
    description = plugin.describe()
    assert description["ready"] is False
    assert description["services"] == []
    assert description["status"]["state"] == "pending"


def test_describe_ready_when_authorized(fake_broker):
    secrets.set_settings("google_drive_read", {"auth_profile": "bus:google"})
    fake_broker.auth_status["bus:google"] = {"state": "ready"}
    plugin.register_broker(fake_broker)

    description = plugin.describe()
    assert description["ready"] is True
    assert "google.drive.read" in description["provides"]
    assert set(description["services"]) == {
        "google.drive.files.list",
        "google.drive.files.get",
    }
    assert description["status"]["state"] == "ready"


