
from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import CurrentUser, DbSession, require_role
from app.features.rentals import schemas, service
from app.features.rentals.state_machine import perform_move
from app.models.rental import RentalState


router = APIRouter(prefix="/rentals", tags=["Rentals"])


@router.post("", response_model=schemas.RentalRead, status_code=status.HTTP_201_CREATED)
def create_rental(payload: schemas.RentalCreate, db: DbSession, user: CurrentUser):
    return service.create_rental(
        db,
        customer_id=user.id,
        car_id=payload.car_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )


@router.get("/{rental_id}", response_model=schemas.RentalRead)
def get_rental(db: DbSession, rental_id: int, *, requester: CurrentUser):
    rental = service.get_rental(db, rental_id)
    if rental is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"rental {rental_id} not found")
    if requester.role == "customer" and rental.customer_id != requester.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not your rental")
    return rental


@router.post(
    "/{rental_id}/return", response_model=schemas.RentalRead,
    dependencies=[require_role("agent")],
)
def return_rental(
    rental_id: int, payload: schemas.RentalReturn, db: DbSession, user: CurrentUser
):
    return perform_move(
        db,
        rental_id,
        RentalState.RETURNED,
        actor=user,
        damage_charge=payload.damage_charge,
        payment_method=payload.payment_method,
    )


@router.post(
    "/{rental_id}/pickup", response_model=schemas.RentalRead,
    dependencies=[require_role("agent")],
)
def pickup(
    rental_id: int,
    db: DbSession,
    user: CurrentUser,
    payload: schemas.RentalPickup | None = None,
):
    return perform_move(
        db,
        rental_id,
        RentalState.ACTIVE,
        actor=user,
        mileage=payload.mileage if payload else None,
    )


@router.post(
    "/{rental_id}/cancel", response_model=schemas.RentalRead,
)
def cancel(rental_id: int, db: DbSession, user: CurrentUser):
    return perform_move(db, rental_id, RentalState.CANCELLED, actor=user)