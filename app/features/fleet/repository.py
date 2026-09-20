"""Read-only query for the fleet board. No writes happen here — this
feature only ever reads."""

from sqlmodel import Session, select

from app.models.car import Car


def list_all_cars(db: Session) -> list[Car]:
    return list(db.exec(select(Car).order_by(Car.plate_no)))