"""Google Drive read-only plugin implementation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Mapping, Optional

from core.contracts.plugin_v2 import PluginDescription, PluginStatus
from core.conn_broker import AuthorizationError, BrokerHandle, BrokerInterface, BrokerRequest
from core import secrets

from . import PLUGIN_ID, PROVIDES, VERSION

DEFAULT_AUTH_PROFILE = "bus:google"
AUTH_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

# Broker-scoped constants
_REQUEST_TIMEOUT = 5.0
_RESPONSE_SIZE_LIMIT = 5 * 1024 * 1024


class PolicyError(RuntimeError):
    """Raised when a request violates configured policy."""


@dataclass
class GoogleDriveHandle:
    """Runtime handle bound to a broker authorization context."""

    broker_handle: BrokerHandle
    broker: BrokerInterface
    settings: Mapping[str, Any]

    def ensure_ready(self, timeout: float = 1.0) -> None:
        self.broker.ensure_ready(self.broker_handle, timeout)

    @property
    def folder_allowlist(self) -> Optional[List[str]]:
        values = self.settings.get("folder_allowlist")
        if not values:
            return None
        return [str(v) for v in values]

    @property
    def mime_allowlist(self) -> Optional[List[str]]:
        values = self.settings.get("mime_allowlist")
        if not values:
            return None
        return [str(v) for v in values]

    @property
    def max_page_size(self) -> int:
        max_configured = int(self.settings.get("max_page_size", 200))
        return max(1, min(200, max_configured))

    def enforce_folder_policy(self, folder_id: Optional[str]) -> None:
        allowlist = self.folder_allowlist
        if allowlist is None or folder_id is None:
            return
        if folder_id not in allowlist:
            raise PolicyError(f"Folder '{folder_id}' is not in the configured allow-list")

    def enforce_mime_policy(self, mime_types: Iterable[str]) -> None:
        allowlist = self.mime_allowlist
        if allowlist is None:
            return
        invalid = [mime for mime in mime_types if mime not in allowlist]
        if invalid:
            raise PolicyError(
                "One or more MIME types are outside the configured allow-list: "
                + ", ".join(sorted(set(invalid)))
            )

    def prepare_request(self, request: BrokerRequest) -> BrokerRequest:
        request = dict(request)
        request.setdefault("timeout", _REQUEST_TIMEOUT)
        request.setdefault("response_size_limit", _RESPONSE_SIZE_LIMIT)
        return request  # type: ignore[return-value]


class GoogleDriveProvider:
    """Provider used by Core to construct broker handles."""

    def __init__(self, broker: BrokerInterface, settings_loader: Callable[[], Mapping[str, Any]]):
        self._broker = broker
        self._settings_loader = settings_loader

    def build_handle(self) -> GoogleDriveHandle:
        settings = self._settings_loader()
        auth_profile = str(settings.get("auth_profile", DEFAULT_AUTH_PROFILE))
        broker_handle = self._broker.get_handle(auth_profile, AUTH_SCOPES)
        return GoogleDriveHandle(broker_handle=broker_handle, broker=self._broker, settings=settings)


_broker: Optional[BrokerInterface] = None


def _load_settings() -> Mapping[str, Any]:
    return secrets.get_settings(PLUGIN_ID)


def describe() -> PluginDescription:
    """Return plugin description gating readiness on auth state."""
    settings = _load_settings()
    auth_profile = str(settings.get("auth_profile", DEFAULT_AUTH_PROFILE))

    description: PluginDescription = {
        "id": PLUGIN_ID,
        "version": VERSION,
        "ready": False,
        "provides": [],
        "services": [],
        "status": {"state": "pending", "message": "Authorization not yet established"},
    }

    if _broker is None:
        description["status"] = {
            "state": "pending",
            "message": "Broker not registered",
        }
        return description

    auth_status = _broker.get_auth_status(auth_profile, AUTH_SCOPES)
    state = auth_status.get("state", "pending")
    message = auth_status.get("message") or "Authorization pending"

    if state == "ready":
        description.update(
            {
                "ready": True,
                "provides": list(PROVIDES),
                "services": [
                    "google.drive.files.list",
                    "google.drive.files.get",
                ],
                "status": {"state": "ready", "message": "Authorization ready"},
            }
        )
    elif state == "pending":
        description["status"] = {"state": "pending", "message": message}
    else:
        description["status"] = {"state": "error", "message": message}

    return description


def register_broker(broker: BrokerInterface) -> GoogleDriveProvider:
    """Register the connection broker with the plugin."""
    global _broker
    _broker = broker
    provider = GoogleDriveProvider(broker=broker, settings_loader=_load_settings)
    return provider


def build_handle() -> GoogleDriveHandle:
    if _broker is None:
        raise RuntimeError("Broker not registered")
    provider = GoogleDriveProvider(broker=_broker, settings_loader=_load_settings)
    return provider.build_handle()


def probe(handle: GoogleDriveHandle) -> PluginStatus:
    """Perform a lightweight readiness probe using the broker."""
    try:
        handle.ensure_ready(timeout=1.0)
    except AuthorizationError as exc:
        return {"state": "blocked", "message": str(exc)}
    return {"state": "ready", "message": "Authorization confirmed"}


__all__ = [
    "AUTH_SCOPES",
    "DEFAULT_AUTH_PROFILE",
    "GoogleDriveHandle",
    "GoogleDriveProvider",
    "PolicyError",
    "build_handle",
    "describe",
    "probe",
    "register_broker",
]

