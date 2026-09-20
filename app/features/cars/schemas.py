from datetime import datetime
from decimal import Decimal

from pydantic import model_validator
from sqlmodel import SQLModel

from app.models.car import CarStatus


class CarCreate(SQLModel):
    plate_no: str
    car_class: str

    model_config = {
        "json_schema_extra": {
            "example": {"plate_no": "ABC-123-XY", "car_class": "SUV"}
        }
    }


class CarRead(SQLModel):
    id: int
    plate_no: str
    car_class: str
    status: CarStatus
    mileage: int
    
class CarAvailabilityQuery(SQLModel):
    """Query params for GET /cars — validated before the service ever
    runs, so a bad date range never reaches business logic. Raising
    ValueError here is what makes FastAPI return a 422 automatically."""

    car_class: str | None = None
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def check_range(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self

# ---- Pricing -------------------------------------------------------
class PricingUpdate(SQLModel):
    """car_class comes from the URL path (PUT /pricing/{class}), never
    from this body — a single resource shouldn't be nameable two ways
    that could disagree."""
    daily_rate: Decimal
    lateness_fee: Decimal

    model_config = {
        "json_schema_extra": {
            "example": {"daily_rate": "15000.00", "lateness_fee": "2500.00"}
        }
    }


class PricingRead(SQLModel):
    id: int
    car_class: str
    daily_rate: Decimal
    lateness_fee: Decimal