import asyncio
import json

from app.events.broadcaster import Broadcaster
from app.integrations.email import send_email
from app.integrations.events import publish_rental_state_changed
from app.integrations.firestore import save_document


def test_save_document_returns_contract_payload():
    result = save_document(
        "audit_logs",
        "rental-42",
        {"rental_id": 42, "status": "changed"},
    )

    assert result["collection"] == "audit_logs"
    assert result["document_id"] == "rental-42"
    assert result["payload"]["rental_id"] == 42
    assert result["status"] == "stubbed"


def test_send_email_returns_contract_payload():
    result = send_email(
        to_email="customer@example.com",
        subject="Welcome",
        body="Hello there",
    )

    assert result["to"] == "customer@example.com"
    assert result["subject"] == "Welcome"
    assert result["body"] == "Hello there"
    assert result["provider"] == "smtp"
    assert "status" in result


def test_send_email_allows_blank_credentials_for_local_smtp(monkeypatch):
    class FakeSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port
            self.sent = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def send_message(self, message):
            self.sent = message

    monkeypatch.setattr("app.integrations.email.settings.smtp_host", "localhost")
    monkeypatch.setattr("app.integrations.email.settings.smtp_port", 1025)
    monkeypatch.setattr("app.integrations.email.settings.smtp_username", "")
    monkeypatch.setattr("app.integrations.email.settings.smtp_password", "")
    monkeypatch.setattr("app.integrations.email.settings.smtp_from_email", "no-reply@fleetgo.local")
    monkeypatch.setattr("app.integrations.email.smtplib.SMTP", FakeSMTP)

    result = send_email(
        to_email="customer@example.com",
        subject="Welcome",
        body="Hello there",
    )

    assert result["status"] == "sent"
    assert result["to"] == "customer@example.com"


def test_publish_rental_state_changed_emits_expected_payload():
    broadcaster = Broadcaster()

    async def collect_event():
        async for raw in broadcaster.subscribe():
            payload = json.loads(raw.removeprefix("data: ").strip())
            return payload

    async def run_case():
        consumer = asyncio.create_task(collect_event())
        await asyncio.sleep(0)
        publish_rental_state_changed(
            rental_id=42,
            car_id=7,
            from_state="reserved",
            to_state="active",
            broadcaster=broadcaster,
        )
        return await asyncio.wait_for(consumer, timeout=1)

    payload = asyncio.run(run_case())

    assert payload["type"] == "rental.state_changed"
    assert payload["id"] == "42"
    assert payload["data"]["rental_id"] == 42
    assert payload["data"]["car_id"] == 7
    assert payload["data"]["from"] == "reserved"
    assert payload["data"]["to"] == "active"
