"""Thin event integration wrappers for the app.

The project keeps business logic in services/state machines and uses this
module to isolate external event concerns.
"""

from __future__ import annotations

from typing import Any

from app.events.broadcaster import Broadcaster, fleet_broadcaster


def publish_rental_state_changed(
    rental_id: int,
    car_id: int,
    from_state: str,
    to_state: str,
    broadcaster: Broadcaster | None = None,
) -> dict[str, Any]:
    """Publish a rental state change event using the shared broadcaster.

    Keeping this function in the integrations layer makes it easy to swap the
    transport later without changing the domain logic that emits it.
    """
    target = broadcaster or fleet_broadcaster
    payload = {
        "rental_id": rental_id,
        "car_id": car_id,
        "from": from_state,
        "to": to_state,
    }
    target.publish("rental.state_changed", str(rental_id), payload)
    return payload
