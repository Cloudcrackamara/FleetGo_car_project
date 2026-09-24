from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlmodel import Session

from app.features.cars import service as cars_service
from app.features.workshop import repository
from app.models.car import Car
from app.models.workshop_visit import WorkshopVisit


def send_to_workshop(
    db: Session,
    car_id: int,
    *,
    comment: str | None = None,
) -> Car:
    if repository.get_open_for_car(db, car_id) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"car {car_id} already has an open workshop visit",
        )

    car = cars_service.send_to_workshop(db, car_id)
    visit = WorkshopVisit(car_id=car_id, comment=comment)
    repository.create(db, visit)
    db.commit()
    db.refresh(car)
    return car


def return_from_workshop(
    db: Session,
    car_id: int,
    *,
    comment: str | None = None,
) -> Car:
    visit = repository.get_open_for_car(db, car_id)
    if visit is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"car {car_id} has no open workshop visit to close",
        )

    if comment is not None:
        visit.comment = (
            comment if visit.comment is None else f"{visit.comment}; {comment}"
        )

    car = cars_service.return_from_workshop(db, car_id)
    repository.close(db, visit, closed_at=datetime.now(UTC))
    db.commit()
    db.refresh(car)
    return car
