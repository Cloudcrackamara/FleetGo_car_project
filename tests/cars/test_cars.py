from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.features.cars.service import create_car, search_available_cars, set_pricing
from app.models.car import Car, CarStatus
from app.models.pricing import Pricing
from app.models.rental import Rental, RentalState
from app.models.user import User


def test_create_car_persists_available_car_with_zero_mileage(db):
	car = create_car(db, plate_no="ABC-123-CAR", car_class="SUV")

	stored = db.get(Car, car.id)
	assert stored is not None
	assert stored.plate_no == "ABC-123-CAR"
	assert stored.status == CarStatus.AVAILABLE
	assert stored.mileage == 0


def test_create_car_rejects_duplicate_plate(db):
	create_car(db, plate_no="DUP-123-CAR", car_class="ECONOMY")

	with pytest.raises(HTTPException) as error:
		create_car(db, plate_no="DUP-123-CAR", car_class="SUV")

	assert error.value.status_code == 409


def test_search_available_cars_excludes_overlapping_rentals(db):
	customer = User(
		email="car-search@example.com",
		password_hash="not-used-in-this-test",
	)
	db.add(customer)
	db.commit()
	db.refresh(customer)

	booked = create_car(db, plate_no="BOOKED-123", car_class="SUV")
	free = create_car(db, plate_no="FREE-123", car_class="SUV")
	start = datetime(2026, 10, 1, tzinfo=UTC)
	end = start + timedelta(days=2)
	db.add(
		Rental(
			customer_id=customer.id,
			car_id=booked.id,
			start_at=start,
			end_at=end,
			state=RentalState.RESERVED,
		)
	)
	db.commit()

	available = search_available_cars(
		db, car_class="SUV", start=start, end=end
	)

	assert {car.id for car in available} == {free.id}


def test_set_pricing_creates_then_updates_one_class(db):
	created = set_pricing(
		db,
		"SUV",
		daily_rate=Decimal("15000.00"),
		lateness_fee=Decimal("2500.00"),
	)
	updated = set_pricing(
		db,
		"SUV",
		daily_rate=Decimal("17500.00"),
		lateness_fee=Decimal("3000.00"),
	)

	rows = db.exec(select(Pricing).where(Pricing.car_class == "SUV")).all()
	assert updated.id == created.id
	assert len(rows) == 1
	assert rows[0].daily_rate == Decimal("17500.00")
	assert rows[0].lateness_fee == Decimal("3000.00")
