from sqlmodel import Session, select

from app.models.payment import Payment
from app.models.rental import Rental

"""Every database query for Payment, in one place."""

# TODO: once app/features/rentals/repository.py exists, delete
# get_rental() below and import app.features.rentals.repository.get
# instead — this is a stand-in only because Rentals isn't built yet,
# and having the same query in two places is exactly the kind of
# duplication that drifts out of sync later.


def get_rental(db: Session, rental_id: int) -> Rental | None:
    return db.get(Rental, rental_id)


def create(db: Session, payment: Payment) -> Payment:
    db.add(payment)
    db.flush()
    return payment


def list_for_rental(db: Session, rental_id: int) -> list[Payment]:
    return list(
        db.exec(select(Payment).where(Payment.rental_id == rental_id))
    )