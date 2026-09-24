import hashlib
import hmac
import json

from sqlmodel import select

from app.core.config import settings
from app.models.processed_event import ProcessedEvent


def signed_headers(body: bytes):
	signature = hmac.new(
		settings.webhook_secret.encode(), body, hashlib.sha256
	).hexdigest()
	return {"x-signature": signature}


def webhook_body(*, event_id="evt-123", reference="999999"):
	return json.dumps(
		{
			"event_id": event_id,
			"type": "payment.succeeded",
			"reference": reference,
			"amount": "25000.00",
			"currency": "XAF",
			"paid_at": "2026-10-01T10:00:00Z",
		},
		separators=(",", ":"),
	).encode()


def test_payment_webhook_rejects_invalid_signature(client):
	body = webhook_body()

	response = client.post(
		"/api/v1/webhooks/payment",
		content=body,
		headers={"x-signature": "invalid"},
	)

	assert response.status_code == 401
	assert response.json()["detail"] == "invalid signature"


def test_payment_webhook_records_orphan_event(client, db):
	body = webhook_body(event_id="evt-orphan", reference="missing-rental")

	response = client.post(
		"/api/v1/webhooks/payment",
		content=body,
		headers=signed_headers(body),
	)

	assert response.status_code == 200
	assert response.json() == {
		"status": "orphan",
		"reference": "missing-rental",
	}
	event = db.exec(
		select(ProcessedEvent).where(ProcessedEvent.event_id == "evt-orphan")
	).one()
	assert event.reference == "missing-rental"


def test_payment_webhook_is_idempotent_for_duplicate_event(client):
	body = webhook_body(event_id="evt-duplicate")
	headers = signed_headers(body)

	first = client.post(
		"/api/v1/webhooks/payment", content=body, headers=headers
	)
	second = client.post(
		"/api/v1/webhooks/payment", content=body, headers=headers
	)

	assert first.status_code == 200
	assert first.json()["status"] == "orphan"
	assert second.status_code == 200
	assert second.json() == {"status": "already processed"}
