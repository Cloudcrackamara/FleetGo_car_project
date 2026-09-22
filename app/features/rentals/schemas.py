from datetime import datetime
from decimal import Decimal

from pydantic import model_validator
from sqlmodel import Field, SQLModel

from app.models.payment import PaymentMethod
from app.models.rental import RentalState


class RentalCreate(SQLModel):
    car_id: int
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def check_range(self):
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "car_id": 1,
                "start_at": "2026-10-03T10:00:00",
                "end_at": "2026-10-05T10:00:00",
            }
        }
    }


class RentalRead(SQLModel):
    id: int
    customer_id: int
    car_id: int
    start_at: datetime
    end_at: datetime
    state: RentalState
    total: Decimal


class RentalReturn(SQLModel):
    damage_charge: Decimal = Field(default=Decimal("0"), ge=0)
    payment_method: PaymentMethod = PaymentMethod.CASH

    model_config = {
        "json_schema_extra": {
            "example": {
                "damage_charge": "5000.00",
                "payment_method": "card",
            }
        }
    }
