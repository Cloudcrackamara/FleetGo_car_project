
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.features.rentals import pricing, repository
from app.models.pricing import Pricing
from app.models.rental import Rental, RentalState
from app.models.state_history import StateHistory
from app.models.user import User

ALLOWED_MOVES: set[tuple[RentalState, RentalState]] = {
    (RentalState.RESERVED, RentalState.ACTIVE),
    (RentalState.ACTIVE, RentalState.RETURNED),
    (RentalState.RESERVED, RentalState.CANCELLED),
}


def _apply_pickup(db: Session, rental: Rental) -> None:
    pass  # nothing extra — car status is a separate machine (workshop)


def _apply_return(db: Session, rental: Rental) -> None:
    price_row = db.exec(
        select(Pricing).where(Pricing.car_class == rental.car.car_class)
    ).first()
    late_fee = pricing.compute_late_fee(
        rental=rental,
        actual_return_at=datetime.now(UTC),
        late_fee_per_day=price_row.lateness_fee,
    )
    rental.total += late_fee


def _apply_cancel(db: Session, rental: Rental) -> None:
    pass  # car was never taken — nothing to undo


_EFFECTS = {
    RentalState.ACTIVE: _apply_pickup,
    RentalState.RETURNED: _apply_return,
    RentalState.CANCELLED: _apply_cancel,
}


def perform_move(
    db: Session, rental_id: int, target: RentalState, actor: User
) -> Rental:
    rental = repository.get_for_update(db, rental_id)  # the row lock
    if rental is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"rental {rental_id} not found"
        )

    if (rental.state, target) not in ALLOWED_MOVES:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"rental {rental_id} is {rental.state}; cannot move to {target}",
        )

    from_state = rental.state
    _EFFECTS[target](db, rental)  
    db.add(rental)

    db.add(
        StateHistory(
            rental_id=rental.id,
            from_state=from_state,
            to_state=target,
            actor_id=actor.id,
        )
    )

    db.commit()
    db.refresh(rental)
    return rental