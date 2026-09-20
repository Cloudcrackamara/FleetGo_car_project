"""Request and response models for Car and Pricing."""

from decimal import Decimal

from sqlmodel import SQLModel

from app.models.car import CarStatus

# ---- Car -----------------------------------------------------------

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