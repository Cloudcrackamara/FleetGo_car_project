"""Firestore client and writes for the live fleet board and dispatch feed.
Firestore is used only for this feed/board data, per the brief — the
source of truth for everything else stays in PostgreSQL."""

from datetime import UTC, datetime

from google.cloud import firestore

from app.core.config import settings

_db = firestore.Client.from_service_account_json(settings.firestore_credentials_path)


def update_fleet_board(car_id: int, status: str, current_rental_id: int | None) -> None:
    _db.collection("fleet_board").document(str(car_id)).set(
        {
            "car_id": car_id,
            "status": status,
            "current_rental_id": current_rental_id,
            "updated_at": datetime.now(UTC).isoformat(),
        }
    )


def append_dispatch_event(event_type: str, car_id: int, data: dict) -> None:
    _db.collection("dispatch_feed").add(
        {
            "type": event_type,
            "car_id": car_id,
            "data": data,
            "at": datetime.now(UTC).isoformat(),
        }
    )