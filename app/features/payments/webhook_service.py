"""Webhook confirmation logic, separate from the person-facing
payment recording in service.py — different caller, different trust
model (signed bytes, not a JWT)."""

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models.processed_event import ProcessedEvent
from app.models.rental import Rental, RentalState


def confirm_payment(db: Session, *, event_id: str, reference: str) -> dict:
    # reference is the rental's id, as a string — the provider echoes
    # back whatever we told it to reference when payment started.
    try:
        rental_id = int(reference)
    except ValueError:
        rental_id = None

    rental = db.get(Rental, rental_id) if rental_id else None

    # INSERT first — the UNIQUE constraint on event_id is the actual
    # guard. Catching IntegrityError is what makes this safe under
    # concurrent duplicate deliveries; a SELECT-then-INSERT has a
    # race window an INSERT-and-catch does not.
    db.add(ProcessedEvent(event_id=event_id, reference=reference))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        # Already processed — same 200, do nothing further. This IS
        # the correct behaviour for a duplicate, not an error case.
        return {"status": "already processed"}

    if rental is None:
        # Unknown reference: still 200 (per the brief), logged as an
        # orphan rather than raising, since the provider isn't at
        # fault for a reference we don't recognise.
        db.commit()
        return {"status": "orphan", "reference": reference}

    if rental.state == RentalState.RESERVED:
        # Nothing to transition — booking already puts a rental in
        # RESERVED. The webhook's job here is just recording that
        # the deposit cleared; see the README note on why there's
        # no separate PENDING state.
        pass

    db.commit()
    return {"status": "confirmed", "rental_id": rental.id}