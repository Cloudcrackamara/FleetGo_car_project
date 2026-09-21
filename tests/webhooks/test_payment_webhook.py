# import hashlib
# import hmac
# import json

# import pytest

# from app.core.config import get_settings


# def create_signature(payload: dict) -> str:
#     settings = get_settings()

#     body = json.dumps(
#         payload,
#         separators=(",", ":"),
#     ).encode()

#     return hmac.new(
#         settings.webhook_signing_secret.encode(),
#         body,
#         hashlib.sha256,
#     ).hexdigest()


# @pytest.mark.asyncio
# async def test_webhook_invalid_signature(client):
#     payload = {
#         "event_id": "event-001",
#         "reference": "rental-001",
#         "amount": "50000",
#     }

#     response = await client.post(
#         "/api/v1/webhooks/payment",
#         json=payload,
#         headers={
#             "X-Webhook-Signature": "wrong-signature",
#         },
#     )

#     assert response.status_code == 401


# @pytest.mark.asyncio
# async def test_webhook_missing_signature(client):
#     payload = {
#         "event_id": "event-002",
#         "reference": "rental-002",
#         "amount": "50000",
#     }

#     response = await client.post(
#         "/api/v1/webhooks/payment",
#         json=payload,
#     )

#     assert response.status_code == 401
