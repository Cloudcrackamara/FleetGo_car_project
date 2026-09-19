# app/models/payment.py
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Numeric
from sqlmodel import Column, Field, SQLModel


class PaymentKind(str, Enum):
    DEPOSIT = "deposit"
    FINAL = "final"


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: int | None = Field(default=None, primary_key=True)
    rental_id: int = Field(foreign_key="rentals.id", index=True)
    kind: PaymentKind
    amount: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    recorded_by: int = Field(foreign_key="users.id")
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))