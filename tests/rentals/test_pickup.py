from datetime import UTC, datetime, timedelta

from app.core.security import hash_password
from app.models import Car, CarClass, CarStatus, Rental, RentalState, Role, User


def create_agent(db):
    agent = User(
        email="agent@test.com",
        password_hash=hash_password("password123"),
        role=Role.AGENT,
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def create_customer(db):
    customer = User(
        email="customer@test.com",
        password_hash=hash_password("password123"),
        role=Role.CUSTOMER,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def create_rental(db, customer):
    car = Car(
        plate_no="PK-001",
        car_class=CarClass.ECONOMY,
        status=CarStatus.AVAILABLE,
    )

    db.add(car)
    db.flush()

    rental = Rental(
        customer_id=customer.id,
        car_id=car.id,
        start_at=datetime.now(UTC),
        end_at=datetime.now(UTC) + timedelta(days=3),
        state=RentalState.RESERVED,
        total=0,
    )

    db.add(rental)
    db.commit()
    db.refresh(rental)
    return rental


def test_pickup_changes_reserved_to_active(client, db):
    agent = create_agent(db)
    customer = create_customer(db)
    rental = create_rental(db, customer)

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": agent.email,
            "password": "password123",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.post(
        f"/api/v1/rentals/{rental.id}/pickup",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "mileage": 10000,
            "condition": "Good condition",
        },
    )

    assert response.status_code == 200
    assert response.json()["state"] == RentalState.ACTIVE.value
    car = db.get(Car, rental.car_id)
    assert car is not None
    assert car.mileage == 10000


def test_pickup_from_returned_rental_fails(client, db):
    agent = create_agent(db)
    customer = create_customer(db)
    rental = create_rental(db, customer)

    rental.state = RentalState.RETURNED
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
        f"/api/v1/rentals/{rental.id}/pickup",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "mileage": 10000,
            "condition": "Good",
        },
    )

    assert response.status_code == 409
