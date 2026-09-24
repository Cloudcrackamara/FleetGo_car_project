from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.features.cars.service import create_car
from app.features.payments.service import record_payment
from app.models.payment import Payment, PaymentKind, PaymentMethod
from app.models.rental import Rental, RentalState
from app.models.user import User


def create_rental(db, *, state=RentalState.RESERVED):
	customer = User(
		email=f"payment-{state.value}@example.com",
		password_hash="not-used-in-this-test",
	)
	db.add(customer)
	db.commit()
	db.refresh(customer)

	car = create_car(
		db,
		plate_no=f"PAY-{state.value.upper()}-CAR",
		car_class="SUV",
	)
	rental = Rental(
		customer_id=customer.id,
		car_id=car.id,
		start_at=datetime(2026, 10, 1, 10, tzinfo=UTC),
		end_at=datetime(2026, 10, 3, 10, tzinfo=UTC),
		state=state,
	)
	db.add(rental)
	db.commit()
	db.refresh(rental)
	return rental


def test_record_payment_persists_payment_and_notifies_customer(db, monkeypatch):
	rental = create_rental(db)
	captured = {}

	def fake_send_customer_email(*args, **kwargs):
		captured["args"] = args
		captured["kwargs"] = kwargs

	monkeypatch.setattr(
		"app.features.payments.service.send_customer_email",
		fake_send_customer_email,
	)

	payment = record_payment(
		db,
		rental_id=rental.id,
		kind=PaymentKind.DEPOSIT,
		method=PaymentMethod.CARD,
		amount=Decimal("25000.00"),
		recorded_by=42,
	)

	stored = db.get(Payment, payment.id)
	assert stored is not None
	assert stored.rental_id == rental.id
	assert stored.kind == PaymentKind.DEPOSIT
	assert stored.method == PaymentMethod.CARD
	assert stored.amount == Decimal("25000.00")
	assert stored.recorded_by == 42
	assert captured["args"] == ("payment-reserved@example.com", "payment_received")
	assert captured["kwargs"]["rental_id"] == rental.id


def test_record_payment_rejects_missing_rental(db):
	with pytest.raises(HTTPException) as error:
		record_payment(
			db,
			rental_id=999999,
			kind=PaymentKind.FINAL,
			method=PaymentMethod.CASH,
			amount=Decimal("100.00"),
			recorded_by=42,
		)

	assert error.value.status_code == 404


@pytest.mark.parametrize("state", [RentalState.CANCELLED, RentalState.RETURNED])
def test_record_payment_rejects_terminal_rental(db, state):
	rental = create_rental(db, state=state)

	with pytest.raises(HTTPException) as error:
		record_payment(
			db,
			rental_id=rental.id,
			kind=PaymentKind.FINAL,
			method=PaymentMethod.CASH,
			amount=Decimal("100.00"),
			recorded_by=42,
		)

	assert error.value.status_code == 409
