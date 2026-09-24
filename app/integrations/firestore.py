"""Firestore integration adapter.

This is intentionally a lightweight wrapper so persistence logic can later be
replaced with a real Firestore client without affecting domain behavior.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def save_document(
    collection: str,
    document_id: str,
    payload: dict[str, Any],
    *,
    client: Any | None = None,
) -> dict[str, Any]:
    """Store a document in a Firestore-like collection.

    The real implementation can later replace this stub without affecting the
    business layer that emits state changes and audit records.
    """
    result = {
        "collection": collection,
        "document_id": document_id,
        "payload": payload,
        "status": "stubbed",
    }
    if client is not None:
        result["status"] = "sent"
    return result


def log_rental_state_change(
    *,
    rental_id: int,
    car_id: int,
    from_state: str,
    to_state: str,
    client: Any | None = None,
) -> dict[str, Any]:
    """Persist a rental audit record in Firestore-compatible format."""
    payload = {
        "rental_id": rental_id,
        "car_id": car_id,
        "from": from_state,
        "to": to_state,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    return save_document(
        "rental_state_history",
        f"rental-{rental_id}",
        payload,
        client=client,
    )
