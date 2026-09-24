"""Firestore client and writes for the live fleet board and dispatch feed.
Firestore is used only for this feed/board data, per the brief — the
source of truth for everything else stays in PostgreSQL.

Mirrors the email adapter's pattern: when Firestore isn't configured
(no credentials path, or the file doesn't exist — e.g. in tests), writes
are stubbed instead of crashing the caller.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from google.cloud import firestore

from app.core.config import settings

_client: firestore.Client | None = None


def _get_client() -> firestore.Client | None:
    global _client
    if _client is not None:
        return _client
    path = settings.firestore_credentials_path
    if not path or not Path(path).exists():
        return None
    _client = firestore.Client.from_service_account_json(path)
    return _client


def save_document(collection: str, document_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Write a document to Firestore. Falls back to a stubbed result when
    Firestore isn't configured/available, so tests and local dev without
    a key don't crash."""
    result: dict[str, Any] = {
        "collection": collection,
        "document_id": document_id,
        "payload": payload,
    }

    client = _get_client()
    if client is None:
        result["status"] = "stubbed"
        result["detail"] = "Firestore is not configured; document was not written."
        return result

    try:
        client.collection(collection).document(document_id).set(
            {**payload, "updated_at": datetime.now(UTC).isoformat()}
        )
        result["status"] = "written"
        return result
    except Exception as exc:  # pragma: no cover - real network path is environment-specific
        result["status"] = "failed"
        result["detail"] = str(exc)
        return result


def update_fleet_board(car_id: int, status: str, current_rental_id: int | None) -> dict[str, Any]:
    return save_document(
        "fleet_board",
        str(car_id),
        {
            "car_id": car_id,
            "status": status,
            "current_rental_id": current_rental_id,
        },
    )


def append_dispatch_event(event_type: str, car_id: int, data: dict) -> dict[str, Any]:
    return save_document(
        "dispatch_feed",
        str(uuid4()),
        {
            "type": event_type,
            "car_id": car_id,
            "data": data,
        },
    )