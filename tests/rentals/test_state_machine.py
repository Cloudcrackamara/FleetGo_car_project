
"""The five hard-problem tests. Each sets up its own data — no
shared fixtures holding rentals between tests.
"""

import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, delete
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import create_access_token
from app.models.car import Car
from app.models.pricing import Pricing
from app.models.rental import Rental, RentalState
from app.models.state_history import StateHistory
from app.models.user import User, UserRole

TEST_ENGINE = create_engine(settings.test_database_url, pool_pre_ping=True)


def _make_car_and_pricing(db: Session) -> Car:
    car = Car(plate_no=f"TEST-{id(db)}", car_class="SUV")
    db.add(car)
    db.flush()

    existing = db.exec(select(Pricing).where(Pricing.car_class == "SUV")).first()
    if existing is None:
        pricing = Pricing(
            car_class="SUV",
            daily_rate=Decimal("10000"),
            lateness_fee=Decimal("2500"),
        )
        db.add(pricing)
        db.flush()
    return car


def _make_agent(db: Session) -> User:
    from app.core.security import hash_password

    agent = User(
        email=f"agent{id(db)}@test.com",
        password_hash=hash_password("x"),
        role=UserRole.AGENT,
    )
    db.add(agent)
    db.flush()
    return agent


def _token_for(user: User) -> str:
    return create_access_token(subject=str(user.id), role=user.role.value)


def test_every_allowed_move_succeeds_and_disallowed_returns_409(db, client):
    car = _make_car_and_pricing(db)
    agent = _make_agent(db)
    rental = Rental(
        customer_id=agent.id, car_id=car.id,
        start_at=datetime.now(UTC), end_at=datetime.now(UTC) + timedelta(days=2),
        state=RentalState.RESERVED, total=Decimal("20000"),
    )
    db.add(rental)
    db.commit()
    db.refresh(rental)

    headers = {"Authorization": f"Bearer {_token_for(agent)}"}

    # Allowed: RESERVED -> ACTIVE
    r = client.post(f"/api/v1/rentals/{rental.id}/pickup", headers=headers)
    assert r.status_code == 200
    assert r.json()["state"] == "active"

    # Disallowed: ACTIVE -> ACTIVE (pickup again)
    r = client.post(f"/api/v1/rentals/{rental.id}/pickup", headers=headers)
    assert r.status_code == 409
    assert "active" in r.json()["error"]["message"].lower()

    # Allowed: ACTIVE -> RETURNED
    r = client.post(f"/api/v1/rentals/{rental.id}/return", headers=headers)
    assert r.status_code == 200
    assert r.json()["state"] == "returned"


def test_state_history_rows_equal_accepted_moves(db, client):
    car = _make_car_and_pricing(db)
    agent = _make_agent(db)
    rental = Rental(
        customer_id=agent.id, car_id=car.id,
        start_at=datetime.now(UTC), end_at=datetime.now(UTC) + timedelta(days=1),
        state=RentalState.RESERVED, total=Decimal("10000"),
    )
    db.add(rental)
    db.commit()
    db.refresh(rental)

    headers = {"Authorization": f"Bearer {_token_for(agent)}"}

    client.post(
        f"/api/v1/rentals/{rental.id}/pickup",
        headers=headers,
    )  # accepted
    client.post(
        f"/api/v1/rentals/{rental.id}/pickup",
        headers=headers,
    )  # refused, no new row
    client.post(
        f"/api/v1/rentals/{rental.id}/return",
        headers=headers,
    )  # accepted

    rows = db.exec(
        select(StateHistory).where(StateHistory.rental_id == rental.id)
    ).all()
    assert len(rows) == 2  # only the two accepted moves


def test_cancelling_after_pickup_returns_409(db, client):
    car = _make_car_and_pricing(db)
    agent = _make_agent(db)
    rental = Rental(
        customer_id=agent.id, car_id=car.id,
        start_at=datetime.now(UTC), end_at=datetime.now(UTC) + timedelta(days=1),
        state=RentalState.RESERVED, total=Decimal("10000"),
    )
    db.add(rental)
    db.commit()
    db.refresh(rental)

    headers = {"Authorization": f"Bearer {_token_for(agent)}"}
    client.post(f"/api/v1/rentals/{rental.id}/pickup", headers=headers)

    r = client.post(f"/api/v1/rentals/{rental.id}/cancel", headers=headers)
    assert r.status_code == 409


def test_late_fee_correct_for_a_late_return_and_zero_on_time():
    """Pure function test — no HTTP, no DB. Same pattern as our
    manual shell check, just automated."""
    from app.features.rentals.pricing import compute_late_fee

    rental = Rental(
        id=0, customer_id=0, car_id=0,
        start_at=datetime(2026, 10, 1), end_at=datetime(2026, 10, 5, 10, 0),
        state=RentalState.ACTIVE, total=Decimal("0"),
    )

    on_time = compute_late_fee(
        rental=rental, actual_return_at=datetime(2026, 10, 5, 10, 0),
        late_fee_per_day=Decimal("2500"),
    )
    assert on_time == Decimal("0")

    two_days_late = compute_late_fee(
        rental=rental, actual_return_at=datetime(2026, 10, 7, 10, 0),
        late_fee_per_day=Decimal("2500"),
    )
    assert two_days_late == Decimal("5000")


def test_two_simultaneous_pickups_produce_exactly_one_active():
    """The genuinely hard one. A normal pytest test runs everything
    on one connection inside one transaction — that CANNOT produce a
    real row-lock race, because there's only ever one session. To
    prove the lock works, we need two REAL, separately-committed
    database sessions racing each other — so this test talks to the
    engine directly, outside the usual rolled-back `db` fixture, and
    cleans up after itself explicitly.
    """
    from app.features.rentals.state_machine import perform_move

    with Session(TEST_ENGINE) as setup_db:
        car = _make_car_and_pricing(setup_db)
        agent = _make_agent(setup_db)
        rental = Rental(
            customer_id=agent.id, car_id=car.id,
            start_at=datetime.now(UTC), end_at=datetime.now(UTC) + timedelta(days=1),
            state=RentalState.RESERVED, total=Decimal("10000"),
        )
        setup_db.add(rental)
        setup_db.commit()
        setup_db.refresh(rental)
        rental_id = rental.id
        agent_id = agent.id
        car_id = car.id

    results = []

    def attempt_pickup():
        with Session(TEST_ENGINE) as thread_db:
            # rebuild a lightweight actor object with just what
            # perform_move needs
            class Actor:
                id = agent_id
            try:
                perform_move(thread_db, rental_id, RentalState.ACTIVE, actor=Actor())
                results.append("success")
            except Exception:
                results.append("conflict")

    t1 = threading.Thread(target=attempt_pickup)
    t2 = threading.Thread(target=attempt_pickup)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results.count("success") == 1
    assert results.count("conflict") == 1

    with Session(TEST_ENGINE) as cleanup_db:
        cleanup_db.exec(
            delete(StateHistory).where(StateHistory.rental_id == rental_id)
        )
        cleanup_db.delete(cleanup_db.get(Rental, rental_id))
        cleanup_db.delete(cleanup_db.get(Car, car_id))
        cleanup_db.commit()