from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.features.rentals import pricing, repository
from app.integrations.events import publish_rental_state_changed
from app.integrations.firestore import log_rental_state_change
from app.models.car import Car
from app.models.payment import Payment, PaymentKind, PaymentMethod
from app.models.pricing import Pricing
from app.models.rental import Rental, RentalState
from app.models.state_history import StateHistory
from app.models.user import User
from app.core.redis_client import redis_client
from app.features.fleet.service import FLEET_BOARD_CACHE_KEY

ALLOWED_MOVES: set[tuple[RentalState, RentalState]] = {
    (RentalState.RESERVED, RentalState.ACTIVE),
    (RentalState.ACTIVE, RentalState.RETURNED),
    (RentalState.RESERVED, RentalState.CANCELLED),
}


def _apply_pickup(
    db: Session,
    rental: Rental,
    damage_charge: Decimal,
    actor: User,
    payment_method: PaymentMethod,
) -> None:
    # No additional side effects required for pickup.
    pass


def _apply_return(
    db: Session,
    rental: Rental,
    damage_charge: Decimal,
    actor: User,
    payment_method: PaymentMethod,
) -> None:
    car = db.get(Car, rental.car_id)

    if car is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"car {rental.car_id} not found for rental {rental.id}",
        )

    price_row = db.exec(
        select(Pricing).where(
            Pricing.car_class == car.car_class
        )
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

    rental.total += late_fee + damage_charge

    if damage_charge > 0:
        db.add(
            Payment(
                rental_id=rental.id,
                kind=PaymentKind.DAMAGE,
                method=payment_method,
                amount=damage_charge,
                recorded_by=actor.id,
            )
        )


def _apply_cancel(
    db: Session,
    rental: Rental,
    damage_charge: Decimal,
    actor: User,
    payment_method: PaymentMethod,
) -> None:
    # Reservation was cancelled before completion.
    pass


_EFFECTS = {
    RentalState.ACTIVE: _apply_pickup,
    RentalState.RETURNED: _apply_return,
    RentalState.CANCELLED: _apply_cancel,
}


def perform_move(
    db: Session,
    rental_id: int,
    target: RentalState,
    actor: User,
    damage_charge: Decimal = Decimal("0"),
    payment_method: PaymentMethod = PaymentMethod.CASH,
) -> Rental:
    rental = repository.get_for_update(
        db,
        rental_id,
    )

    if rental is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"rental {rental_id} not found",
        )

    if (rental.state, target) not in ALLOWED_MOVES:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"rental {rental_id} is {rental.state}; cannot move to {target}",
        )

    from_state = rental.state
    rental.state = target

    _EFFECTS[target](
        db,
        rental,
        damage_charge,
        actor,
        payment_method,
    )

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

    redis_client.delete(FLEET_BOARD_CACHE_KEY)

    publish_rental_state_changed(
        rental_id=rental.id,
        car_id=rental.car_id,
        from_state=from_state.value,
        to_state=target.value,
    )
    log_rental_state_change(
        rental_id=rental.id,
        car_id=rental.car_id,
        from_state=from_state.value,
        to_state=target.value,
    )

    return rental
