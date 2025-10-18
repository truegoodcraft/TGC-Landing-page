"""Capability manifest for the Google Drive read-only plugin."""
from __future__ import annotations

GOOGLE_DRIVE_READ = {
    "id": "google.drive.read",
    "stages": ["service"],
    "trust_tier": "untrusted",
    "services": {
        "google.drive.files.list": {"read": True},
        "google.drive.files.get": {"read": True},
    },
}

__all__ = ["GOOGLE_DRIVE_READ"]

