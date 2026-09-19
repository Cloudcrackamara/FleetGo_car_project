# app/models/workshop_visit.py
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class WorkshopVisit(SQLModel, table=True):
    __tablename__ = "workshop_visits"

    id: int | None = Field(default=None, primary_key=True)
    car_id: int = Field(foreign_key="cars.id", index=True)
    opened_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # null while the car is still in the workshop
    closed_at: datetime | None = Field(default=None)
    comment: str | None = Field(default=None)