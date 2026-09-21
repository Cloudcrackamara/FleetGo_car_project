# app/models/rental.py
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Numeric
from sqlmodel import Column, Field, Index, SQLModel


class RentalState(StrEnum):
    """Exactly the machine on paper. POST /rentals creates the row
    already RESERVED — booking a car holds it immediately; the
    payment webhook records the deposit but does not move the state,
    since there's nothing before RESERVED to move from."""

    RESERVED = "reserved"
    ACTIVE = "active"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class Rental(SQLModel, table=True):
    __tablename__ = "rentals"
    __table_args__ = (
        # The brief names this composite index directly: it's what
        # makes GET /cars?class&start&end fast — checking whether a
        # car has any rental overlapping a date range.
        Index("ix_rentals_car_daterange", "car_id", "start_at", "end_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="users.id", index=True)
    car_id: int = Field(foreign_key="cars.id", index=True)
    start_at: datetime
    end_at: datetime
    state: RentalState = Field(default=RentalState.RESERVED, index=True)
    total: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(10, 2), nullable=False)
    )