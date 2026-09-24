"""Email integration adapter.

This file is intentionally small and focused on transport concerns only. Real
SMTP implementation can be added here without affecting the rest of the app.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from app.core.config import settings


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    sender: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Send an email through SMTP when configured.

    If SMTP is not configured, the adapter keeps the app safe by returning a
    structured dry-run result instead of crashing the caller.
    """
    payload = {
        "to": to_email,
        "subject": subject,
        "body": body,
        "provider": "smtp",
        "meta": kwargs,
    }

    smtp_host = settings.smtp_host
    smtp_username = settings.smtp_username
    smtp_password = settings.smtp_password
    smtp_from_email = sender or settings.smtp_from_email

    if not smtp_host or not smtp_from_email:
        payload["status"] = "stubbed"
        payload["detail"] = "SMTP is not configured; email was not sent."
        return payload

    message = EmailMessage()
    message["From"] = smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(smtp_host, settings.smtp_port) as smtp:
            if smtp_username and smtp_password:
                try:
                    smtp.starttls()
                except smtplib.SMTPNotSupportedError:
                    pass
                smtp.login(smtp_username, smtp_password)
            smtp.send_message(message)
        payload["status"] = "sent"
        return payload
    except Exception as exc:  # pragma: no cover - real network path is environment-specific
        payload["status"] = "failed"
        payload["detail"] = str(exc)
        return payload


def send_rental_confirmation_email(*, to_email: str, customer_name: str, rental_id: int) -> dict[str, Any]:
    """Convenience wrapper for a common integration event.

    Domain code can call this without knowing about SMTP details or provider
    behavior.
    """
    subject = f"Rental confirmation #{rental_id}"
    body = (
        f"Hello {customer_name},\n\n"
        f"Your rental #{rental_id} has been confirmed.\n"
        "We look forward to serving you."
    )
    return send_email(
        to_email=to_email,
        subject=subject,
        body=body,
        renter_name=customer_name,
        rental_id=rental_id,
    )
