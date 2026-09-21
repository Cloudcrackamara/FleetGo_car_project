import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, delete
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import hash_password
from app.features.rentals.state_machine import perform_move
from app.models import Car, Rental, RentalState, User
from app.models.pricing import Pricing
from app.models.state_history import StateHistory

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
    agent = User(
        email=f"agent{id(db)}@test.com",
        password_hash=hash_password("x"),
        role="agent",
    )
    db.add(agent)
    db.flush()
    return agent


def test_two_agents_picking_up_simultaneously():
    with Session(TEST_ENGINE) as setup_db:
        car = _make_car_and_pricing(setup_db)
        agent = _make_agent(setup_db)
        rental = Rental(
            customer_id=agent.id,
            car_id=car.id,
            start_at=datetime.now(UTC),
            end_at=datetime.now(UTC) + timedelta(days=1),
            state=RentalState.RESERVED,
            total=Decimal("10000"),
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
