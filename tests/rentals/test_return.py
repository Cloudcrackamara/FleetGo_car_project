from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.core.security import hash_password
from app.models import (
    Car,
    CarClass,
    CarStatus,
    Payment,
    PaymentKind,
    PaymentMethod,
    Pricing,
    Rental,
    RentalState,
    Role,
    User,
)


def create_agent(db):
    agent = User(
        email=f"agent-{uuid4()}@test.com",
        password_hash=hash_password("password123"),
        role=Role.AGENT,
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def create_active_rental(db):
    customer = User(
        email="customer@test.com",
        password_hash=hash_password("password123"),
        role=Role.CUSTOMER,
    )

    car = Car(
        plate_no="RT-001",
        car_class=CarClass.ECONOMY,
        status=CarStatus.AVAILABLE,
    )

    pricing = Pricing(
        car_class=CarClass.ECONOMY,
        daily_rate=50000,
        lateness_fee=10000,
    )

    db.add(customer)
    db.add(car)
    db.add(pricing)
    db.flush()

    rental = Rental(
        customer_id=customer.id,
        car_id=car.id,
        start_at=datetime.now(UTC) - timedelta(days=5),
        end_at=datetime.now(UTC) - timedelta(days=2),
        state=RentalState.ACTIVE,
        total=0,
    )

    db.add(rental)
    db.commit()
    db.refresh(rental)
    return rental


def test_return_changes_active_to_returned(client, db):
    agent = create_agent(db)
    rental = create_active_rental(db)

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": agent.email,
            "password": "password123",
        },
    )

    token = login.json()["access_token"]

    response = client.post(
        f"/api/v1/rentals/{rental.id}/return",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "mileage": 10500,
            "condition": "Good condition",
            "damage_charge": 0,
        },
    )

    assert response.status_code == 200
    assert response.json()["state"] == RentalState.RETURNED.value
    assert Decimal(response.json()["total"]) >= Decimal("0")


def test_return_records_damage_payment(client, db):
    agent = create_agent(db)
    rental = create_active_rental(db)

    login = client.post(
        "/api/v1/auth/login",
        json={"email": agent.email, "password": "password123"},
    )

    response = client.post(
        f"/api/v1/rentals/{rental.id}/return",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={"damage_charge": "5000.00", "payment_method": "card"},
    )

    assert response.status_code == 200
    payment = db.query(Payment).filter(Payment.rental_id == rental.id).one()
    assert payment.kind == PaymentKind.DAMAGE
    assert payment.method == PaymentMethod.CARD
    assert payment.amount == Decimal("5000.00")
    assert payment.recorded_by == agent.id


def test_return_from_reserved_fails(client, db):
    agent = create_agent(db)

    customer = User(
        email="customer-test@test.com",
        password_hash=hash_password("password123"),
        role=Role.CUSTOMER,
    )

    car = Car(
        plate_no="RS-001",
        car_class=CarClass.ECONOMY,
        status=CarStatus.AVAILABLE,
    )

    db.add(customer)
    db.add(car)
    db.flush()

    rental = Rental(
        customer_id=customer.id,
        car_id=car.id,
        start_at=datetime.now(UTC),
        end_at=datetime.now(UTC) + timedelta(days=2),
        state=RentalState.RESERVED,
        total=0,
    )

    db.add(rental)
    db.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": agent.email,
            "password": "password123",
        },
    )

    token = login.json()["access_token"]

    response = client.post(
        f"/api/v1/rentals/{rental.id}/return",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "mileage": 10000,
            "condition": "Good",
            "damage_charge": 0,
        },
    )

    assert response.status_code == 409
