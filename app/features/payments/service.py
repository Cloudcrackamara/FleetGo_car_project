from decimal import Decimal

from fastapi import HTTPException, status
from sqlmodel import Session

from app.features.payments import repository
from app.integrations.notifications import send_customer_email
from app.models.payment import Payment, PaymentKind, PaymentMethod
from app.models.rental import RentalState
from app.models.user import User


def record_payment(
    db: Session,
    *,
    rental_id: int,
    kind: PaymentKind,
    method: PaymentMethod,
    amount: Decimal,
    recorded_by: int,
) -> Payment:
    rental = repository.get_rental(db, rental_id)
    if rental is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"rental {rental_id} not found",
        )

    if rental.state in (RentalState.CANCELLED, RentalState.RETURNED):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"rental {rental_id} is {rental.state}; cannot record a payment",
        )

    payment = repository.create(
        db,
        Payment(
            rental_id=rental_id,
            kind=kind,
            method=method,
            amount=amount,
            recorded_by=recorded_by,
        ),
    )
    db.commit()
    db.refresh(payment)

    customer = db.get(User, rental.customer_id)
    if customer:
        send_customer_email(
            customer.email,
            "payment_received",
            payment_kind=kind.value,
            amount=amount,
            rental_id=rental_id,
        )

    return payment
