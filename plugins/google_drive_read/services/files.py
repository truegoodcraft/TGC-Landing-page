"""Service implementations for Google Drive file access."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional

from ..plugin import GoogleDriveHandle, PolicyError

_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
_METADATA_FIELDS = "id,name,size,mimeType,owners,modifiedTime,md5Checksum,parents"
_LIST_FIELDS = "files(id,name,mimeType,owners,modifiedTime,parents),nextPageToken"


def _escape(value: str) -> str:
    return value.replace("'", "\\'")


def _build_query(
    folder_id: Optional[str],
    mime_types: Optional[Iterable[str]],
    owners: Optional[Iterable[str]],
    name_contains: Optional[str],
) -> str:
    conditions = ["trashed = false"]
    if folder_id:
        conditions.append(f"'{_escape(folder_id)}' in parents")
    if mime_types:
        items = [f"mimeType = '{_escape(m)}'" for m in mime_types]
        conditions.append("(" + " or ".join(items) + ")")
    if owners:
        items = [f"'{_escape(owner)}' in owners" for owner in owners]
        conditions.append("(" + " or ".join(items) + ")")
    if name_contains:
        conditions.append(f"name contains '{_escape(name_contains)}'")
    return " and ".join(conditions)


def list_files(handle: GoogleDriveHandle, query: Mapping[str, Any]) -> Dict[str, Any]:
    folder_id = query.get("folder_id")
    mime_types = query.get("mime_types")
    owners = query.get("owners")
    name_contains = query.get("name_contains")
    page_size = int(query.get("page_size", 50))
    order_by = query.get("order_by")
    page_token = query.get("page_token")

    if folder_id is not None:
        handle.enforce_folder_policy(str(folder_id))
    if mime_types is not None:
        handle.enforce_mime_policy([str(m) for m in mime_types])

    page_size = max(1, min(page_size, handle.max_page_size))

    drive_query = _build_query(
        folder_id=str(folder_id) if folder_id else None,
        mime_types=[str(m) for m in mime_types] if mime_types else None,
        owners=[str(o) for o in owners] if owners else None,
        name_contains=str(name_contains) if name_contains else None,
    )

    request = handle.prepare_request(
        {
            "method": "GET",
            "url": _DRIVE_FILES_URL,
            "query": {
                "q": drive_query,
                "fields": _LIST_FIELDS,
                "pageSize": str(page_size),
            },
        }
    )

    if order_by:
        request["query"] = dict(request["query"], orderBy=str(order_by))
    if page_token:
        request["query"] = dict(request["query"], pageToken=str(page_token))

    response = handle.broker.request(handle.broker_handle, request)
    return response.get("body", {})


def get_file_metadata(handle: GoogleDriveHandle, file_id: str) -> Dict[str, Any]:
    metadata = _fetch_metadata(handle, file_id)
    _enforce_metadata_policy(handle, metadata)
    return metadata


def _fetch_metadata(handle: GoogleDriveHandle, file_id: str) -> Dict[str, Any]:
    request = handle.prepare_request(
        {
            "method": "GET",
            "url": f"{_DRIVE_FILES_URL}/{file_id}",
            "query": {
                "fields": _METADATA_FIELDS,
            },
        }
    )
    response = handle.broker.request(handle.broker_handle, request)
    body = response.get("body", {})
    if not isinstance(body, dict):
        raise RuntimeError("Unexpected metadata response")
    return body


def _enforce_metadata_policy(handle: GoogleDriveHandle, metadata: Mapping[str, Any]) -> None:
    parents = metadata.get("parents") or []
    mime_type = metadata.get("mimeType")

    if handle.folder_allowlist is not None:
        allowed = set(handle.folder_allowlist)
        if not any(parent in allowed for parent in parents):
            raise PolicyError("File is not located in an allowed folder")

    if handle.mime_allowlist is not None and mime_type is not None:
        handle.enforce_mime_policy([str(mime_type)])


def stream_file(handle: GoogleDriveHandle, file_id: str):
    metadata = _fetch_metadata(handle, file_id)
    _enforce_metadata_policy(handle, metadata)

    request = handle.prepare_request(
        {
            "method": "GET",
            "url": f"{_DRIVE_FILES_URL}/{file_id}",
            "query": {
                "alt": "media",
            },
        }
    )
    return handle.broker.stream(handle.broker_handle, request)


__all__ = [
    "get_file_metadata",
    "list_files",
    "stream_file",
]

