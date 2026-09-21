from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.security import hash_password
from app.models import Car, CarClass, CarStatus, Pricing, RentalState, Role, User


def test_customer_can_create_rental(client, db):
    user = User(
        email=f"customer-{uuid4()}@test.com",
        password_hash=hash_password("password123"),
        role=Role.CUSTOMER,
    )

    car = Car(
        plate_no=f"ABC-{uuid4().hex[:6].upper()}",
        car_class=CarClass.ECONOMY,
        status=CarStatus.AVAILABLE,
    )

    pricing = Pricing(
        car_class=CarClass.ECONOMY,
        daily_rate=50000,
        lateness_fee=10000,
    )

    db.add(user)
    db.add(car)
    db.add(pricing)
    db.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "password123",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    start_at = datetime.now(UTC) + timedelta(days=1)
    end_at = start_at + timedelta(days=3)

    response = client.post(
        "/api/v1/rentals",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "car_id": str(car.id),
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
    )

    assert response.status_code == 201
    assert response.json()["state"] == RentalState.RESERVED.value


def test_rental_end_must_be_after_start(client):
    response = client.post(
        "/api/v1/rentals",
        json={
            "car_id": str(uuid4()),
            "start_at": "2026-09-20T10:00:00Z",
            "end_at": "2026-09-19T10:00:00Z",
        },
    )

    assert response.status_code == 401
