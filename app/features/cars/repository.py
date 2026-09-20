# features/cars/repository.py
"""Every database query for Car, in one place. Nothing outside this
file runs a query against the cars table. Returns rows or None —
never raises HTTP errors, never commits (that's the service's job).
"""

from datetime import datetime

from sqlmodel import Session, select

from app.models.car import Car, CarStatus
from app.models.rental import Rental, RentalState


def get(db: Session, car_id: int) -> Car | None:
    return db.get(Car, car_id)


def get_by_plate(db: Session, plate_no: str) -> Car | None:
    return db.exec(select(Car).where(Car.plate_no == plate_no)).first()


def create(db: Session, car: Car) -> Car:
    db.add(car)
    db.flush()  # assigns car.id without committing — service commits
    return car


def list_all(db: Session, *, car_class: str | None = None) -> list[Car]:
    query = select(Car)
    if car_class:
        query = query.where(Car.car_class == car_class)
    return list(db.exec(query))


def list_available(
    db: Session, *, car_class: str | None, start: datetime, end: datetime
) -> list[Car]:
    """
    Return cars that are available during the requested time window.

    A car is unavailable if:
    - it is IN_WORKSHOP, or
    - it has a RESERVED or ACTIVE rental overlapping the requested window.
    """

    # Find rentals that overlap the requested time window.
    overlapping_rental = (
        select(Rental.id)
        .where(
            Rental.car_id == Car.id,
            Rental.state.in_([RentalState.RESERVED, RentalState.ACTIVE]),
            Rental.start_at < end,
            Rental.end_at > start,
        )
        .exists()
    )

    # Start with all cars, excluding those in the workshop or overlapping.
    statement = select(Car).where(
        Car.status != CarStatus.IN_WORKSHOP,
        ~overlapping_rental,
    )

    # Only filter by class when one was provided.
    if car_class is not None:
        statement = statement.where(Car.car_class == car_class)

    return list(db.exec(statement).all())


def update_status(db: Session, car: Car, status) -> Car:
    car.status = status
    db.add(car)
    db.flush()
    return car


def update_mileage(db: Session, car: Car, mileage: int) -> Car:
    car.mileage = mileage
    db.add(car)
    db.flush()
    return car