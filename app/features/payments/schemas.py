"""Request/response models for recording a rental payment."""

from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel

from app.models.payment import PaymentKind, PaymentMethod


class PaymentCreate(SQLModel):
    kind: PaymentKind
    method: PaymentMethod = PaymentMethod.CASH
    amount: Decimal

    model_config = {
        "json_schema_extra": {
            "example": {
                "kind": "deposit",
                "method": "card",
                "amount": "25000.00",
            }
        }
    }


class PaymentRead(SQLModel):
    id: int
    rental_id: int
    kind: PaymentKind
    method: PaymentMethod
    amount: Decimal
    recorded_by: int
    recorded_at: datetime
