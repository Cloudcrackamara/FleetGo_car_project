
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

from app.models.rental import RentalState

# Append-only in the DATABASE, not just by convention, is a Day 8
# decision (whether to REVOKE UPDATE/DELETE from the app's DB user).
# The columns don't change either way — settle the enforcement
# mechanism when you write lifecycle.py.


class StateHistory(SQLModel, table=True):
    __tablename__ = "state_history"

    id: int | None = Field(default=None, primary_key=True)
    rental_id: int = Field(foreign_key="rentals.id", index=True)
    from_state: RentalState
    to_state: RentalState
    actor_id: int = Field(foreign_key="users.id")
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))