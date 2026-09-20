# This makes alembic discover all models

from app.models import (  # noqa: F401
    car,
    payment,
    pricing,
    processed_event,
    rental,
    state_history,
    user,
    workshop_visit,
)

__all__ = [
    "car",
    "payment",
    "pricing",
    "processed_event",
    "rental",
    "state_history",
    "user",
    "workshop_visit",
]