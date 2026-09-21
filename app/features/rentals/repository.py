
"""Every database query for Rental, in one place."""

from sqlmodel import Session, select

from app.models.rental import Rental


def get(db: Session, rental_id: int) -> Rental | None:
    return db.get(Rental, rental_id)


def get_for_update(db: Session, rental_id: int) -> Rental | None:
    """The locking read — the one the state machine uses, and the
    ONLY place in the codebase that should SELECT ... FOR UPDATE on
    a rental. See state_machine.py for why."""
    statement = select(Rental).where(Rental.id == rental_id).with_for_update()
    return db.exec(statement).first()


def create(db: Session, rental: Rental) -> Rental:
    db.add(rental)
    db.flush()
    return rental


def list_for_customer(
    db: Session, customer_id: int, *, state: str | None = None
) -> list[Rental]:
    statement = select(Rental).where(Rental.customer_id == customer_id)
    if state:
        statement = statement.where(Rental.state == state)
    return list(db.exec(statement))


def list_all(db: Session, *, state: str | None = None) -> list[Rental]:
    statement = select(Rental)
    if state:
        statement = statement.where(Rental.state == state)
    return list(db.exec(statement))