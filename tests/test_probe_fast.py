from __future__ import annotations

import time

from core import secrets
from core.conn_broker import AuthorizationError

from plugins.google_drive_read import plugin


def test_probe_completes_under_two_seconds(fake_broker):
    secrets.set_settings("google_drive_read", {})
    fake_broker.auth_status["bus:google"] = {"state": "ready"}
    provider = plugin.register_broker(fake_broker)
    handle = provider.build_handle()

    start = time.perf_counter()
    status = plugin.probe(handle)
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
    assert status["state"] == "ready"
    assert fake_broker.ensure_ready_called is True


def test_probe_reports_blocked(fake_broker, monkeypatch):
    secrets.set_settings("google_drive_read", {})
    fake_broker.auth_status["bus:google"] = {"state": "ready"}
    provider = plugin.register_broker(fake_broker)
    handle = provider.build_handle()

    def blocked(*args, **kwargs):
        raise AuthorizationError("authorization pending")

    monkeypatch.setattr(fake_broker, "ensure_ready", blocked)

    status = plugin.probe(handle)
    assert status["state"] == "blocked"
    assert "authorization" in status["message"].lower()


