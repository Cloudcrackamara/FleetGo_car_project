from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.features.cars import repository as car_repo
from app.features.cars.repository import get as get_car
from app.features.rentals import pricing, repository
from app.models.pricing import Pricing
from app.models.rental import Rental, RentalState


def create_rental(
    db: Session, *, customer_id: int, car_id: int, start_at: datetime, end_at: datetime
) -> Rental:
    car = get_car(db, car_id)
    if car is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"car {car_id} not found")

    # Reuse the SAME overlap query cars/repository.py already proved
    # correct — do not write this check a second time here.
    available = car_repo.list_available(
        db, car_class=None, start=start_at, end=end_at
    )
    if car not in available:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"car {car_id} is not available for that window"
        )

    price_row = db.exec(
        select(Pricing).where(Pricing.car_class == car.car_class)
    ).first()
    if price_row is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"no pricing set for class {car.car_class}"
        )

    total = pricing.compute_total(
        daily_rate=price_row.daily_rate, start_at=start_at, end_at=end_at
    )

    rental = repository.create(
        db,
        Rental(
            customer_id=customer_id,
            car_id=car_id,
            start_at=start_at,
            end_at=end_at,
            state=RentalState.RESERVED,
            total=total,
        ),
    )
    db.commit()
    db.refresh(rental)
    return rental


def get_rental(db: Session, rental_id: int) -> Rental:
    rental = repository.get(db, rental_id)
    if rental is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"rental {rental_id} not found")
    return rental


def list_rentals(
    db: Session, *, customer_id: int | None, state: str | None
) -> list[Rental]:
    if customer_id is not None:
        return repository.list_for_customer(db, customer_id, state=state)
    return repository.list_all(db, state=state)