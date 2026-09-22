
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.events.broadcaster import fleet_broadcaster
from app.features.rentals import pricing, repository
from app.models.car import Car
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
    # Pickup is the state transition itself; the rental is already marked
    # ACTIVE before this hook is called, and there is no additional
    # persisted payload required by the current contract.
    return None


def _apply_return(db: Session, rental: Rental) -> None:
    car = db.get(Car, rental.car_id)
    if car is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"car {rental.car_id} not found for rental {rental.id}",
        )

    price_row = db.exec(
        select(Pricing).where(Pricing.car_class == car.car_class)
    ).first()
    if price_row is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"no pricing set for class {car.car_class}",
        )

    late_fee = pricing.compute_late_fee(
        rental=rental,
        actual_return_at=datetime.now(UTC),
        late_fee_per_day=price_row.lateness_fee,
    )
    rental.total += late_fee


def _apply_cancel(db: Session, rental: Rental) -> None:
    # Cancel is a terminal transition that does not require extra side effects
    # for this API layer; the state and history record are the important bits.
    return None


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
    rental.state = target
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
    fleet_broadcaster.publish(
        "rental.state_changed",
        str(rental.id),
        {
            "rental_id": rental.id,
            "car_id": rental.car_id,
            "from": from_state.value,
            "to": target.value,
        },
    )
    return rental