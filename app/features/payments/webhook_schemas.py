from decimal import Decimal

from sqlmodel import SQLModel

"""Shape of the payment provider's callback body — dictated by them,
not by us. Separate from payments/schemas.py since it's a different
concern (a machine calling us, not a person)."""


class WebhookPayload(SQLModel):
    event_id: str
    type: str  # e.g. "payment.succeeded"
    reference: str  # which rental/booking this payment belongs to
    amount: Decimal
    currency: str
    paid_at: str