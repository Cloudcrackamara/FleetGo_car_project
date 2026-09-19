# app/models/processed_event.py
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class ProcessedEvent(SQLModel, table=True):
    __tablename__ = "processed_events"

    id: int | None = Field(default=None, primary_key=True)
    # UNIQUE is the actual guard against double-processing the same
    # webhook — insert and catch the violation, never SELECT-then-INSERT
    event_id: str = Field(unique=True, index=True)
    reference: str
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))