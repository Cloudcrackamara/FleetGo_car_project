from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession, require_role
from app.features.payments import schemas, service

"""Nested under /rentals to match the brief's exact path:
POST /api/v1/rentals/{id}/payments — agent only."""

router = APIRouter(prefix="/rentals", tags=["payments"])


@router.post(
    "/{rental_id}/payments",
    response_model=schemas.PaymentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_role("agent")],
)
def record_payment(rental_id: int, payload: schemas.PaymentCreate, db: DbSession, user: CurrentUser):
    return service.record_payment(
        db,
        rental_id=rental_id,
        kind=payload.kind,
        amount=payload.amount,
        recorded_by=user.id,
    )