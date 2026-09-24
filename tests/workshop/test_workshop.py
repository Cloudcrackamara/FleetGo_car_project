from sqlmodel import select

from app.features.cars.service import create_car
from app.features.workshop.service import (
    return_from_workshop,
    send_to_workshop,
)
from app.models.car import CarStatus
from app.models.workshop_visit import WorkshopVisit


def test_send_to_workshop_creates_visit(db):
    car = create_car(db, plate_no="ABC-123-WK", car_class="SUV")

    updated = send_to_workshop(db, car.id)

    assert updated.status == CarStatus.IN_WORKSHOP
    visit = db.exec(
        select(WorkshopVisit).where(WorkshopVisit.car_id == car.id)
    ).first()
    assert visit is not None
    assert visit.closed_at is None


def test_return_from_workshop_closes_last_open_visit(db):
    car = create_car(db, plate_no="XYZ-987-WK", car_class="ECONOMY")
    send_to_workshop(db, car.id)

    updated = return_from_workshop(db, car.id)

    assert updated.status == CarStatus.AVAILABLE
    visit = db.exec(
        select(WorkshopVisit).where(WorkshopVisit.car_id == car.id)
    ).first()
    assert visit is not None
    assert visit.closed_at is not None
