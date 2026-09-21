
from enum import Enum

from sqlmodel import Field, SQLModel


class CarStatus(str, Enum):
    """The car's physical location, not its booking calendar.
    Availability for a date range is answered by querying rentals,
    not by adding more values here."""
    AVAILABLE = "available"
    IN_WORKSHOP = "in_workshop"


class Car(SQLModel, table=True):
    __tablename__ = "cars"

    id: int | None = Field(default=None, primary_key=True)
    plate_no: str = Field(unique=True, index=True)
    car_class: str = Field(index=True)
    status: CarStatus = Field(default=CarStatus.AVAILABLE)
    mileage: int = Field(default=0)