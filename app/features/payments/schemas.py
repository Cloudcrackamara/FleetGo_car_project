"""Request/response models for recording a rental payment."""

from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel

from app.models.payment import PaymentKind


class PaymentCreate(SQLModel):
    kind: PaymentKind
    amount: Decimal

    model_config = {
        "json_schema_extra": {
            "example": {"kind": "deposit", "amount": "25000.00"}
        }
    }


class PaymentRead(SQLModel):
    id: int
    rental_id: int
    kind: PaymentKind
    amount: Decimal
    recorded_by: int
    recorded_at: datetime