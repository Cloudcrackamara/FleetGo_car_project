from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.dependencies import DbSession
from app.core.security import verify_webhook_signature
from app.features.payments import webhook_service
from app.features.payments.webhook_schemas import WebhookPayload

"""Separate router from payments/router.py — this one has NO JWT
auth. The caller proves itself with a signature instead."""

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/payment", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    db: DbSession,
    x_signature: str = Header(...),
):
    raw_body = await request.body()  # MUST read raw bytes before parsing

    if not verify_webhook_signature(raw_body, x_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid signature",
        )

    payload = WebhookPayload.model_validate_json(raw_body)

    return webhook_service.confirm_payment(
        db, event_id=payload.event_id, reference=payload.reference
    )