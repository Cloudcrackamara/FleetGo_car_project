"""Read-only view for the manager's fleet board."""

from sqlmodel import SQLModel

from app.models.car import CarStatus


class FleetBoardRow(SQLModel):
    id: int
    plate_no: str
    car_class: str
    status: CarStatus
    mileage: int

    current_rental_id: int | None = None
    current_rental_state: str | None = None