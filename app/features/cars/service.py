
from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.features.cars import repository
from app.models.car import Car, CarStatus
from app.models.pricing import Pricing
from app.core.redis_client import redis_client
from app.features.fleet.service import FLEET_BOARD_CACHE_KEY


def create_car(db: Session, *, plate_no: str, car_class: str) -> Car:
    if repository.get_by_plate(db, plate_no):
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"a car with plate {plate_no} already exists"
        )
    car = repository.create(db, Car(plate_no=plate_no, car_class=car_class))
    db.commit()
    db.refresh(car)
    return car


def search_available_cars(
    db: Session, *, car_class: str | None, start: datetime, end: datetime
) -> list[Car]:
    return repository.list_available(db, car_class=car_class, start=start, end=end)


def send_to_workshop(db: Session, car_id: int) -> Car:
    car = repository.get(db, car_id)
    if car is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"car {car_id} not found")
    if car.status == CarStatus.IN_WORKSHOP:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"car {car_id} is already in the workshop"
        )
    car = repository.update_status(db, car, CarStatus.IN_WORKSHOP)
    db.commit()
    db.refresh(car)
    redis_client.delete(FLEET_BOARD_CACHE_KEY)
    return car


def return_from_workshop(db: Session, car_id: int) -> Car:
    car = repository.get(db, car_id)
    if car is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"car {car_id} not found")
    if car.status != CarStatus.IN_WORKSHOP:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"car {car_id} is not in the workshop"
        )
    car = repository.update_status(db, car, CarStatus.AVAILABLE)
    db.commit()
    db.refresh(car)
    redis_client.delete(FLEET_BOARD_CACHE_KEY)
    return car


def get_pricing(db: Session, car_class: str) -> Pricing:
    pricing = db.exec(
        select(Pricing).where(Pricing.car_class == car_class)
    ).first()
    if pricing is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"no pricing set for class {car_class}"
        )
    return pricing


def set_pricing(db: Session, car_class: str, *, daily_rate, lateness_fee) -> Pricing:
    pricing = db.exec(
        select(Pricing).where(Pricing.car_class == car_class)
    ).first()
    if pricing is None:
        pricing = Pricing(
            car_class=car_class,
            daily_rate=daily_rate,
            lateness_fee=lateness_fee,
        )
    else:
        pricing.daily_rate = daily_rate
        pricing.lateness_fee = lateness_fee
    db.add(pricing)
    db.commit()
    db.refresh(pricing)
    return pricing