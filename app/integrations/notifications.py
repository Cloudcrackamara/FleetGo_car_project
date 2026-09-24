"""Centralized customer notification templates and dispatch."""

from __future__ import annotations

from typing import Any

from app.integrations.email import send_email


TEMPLATES: dict[str, str] = {
    "welcome": (
        "Hello {customer_email},\n\n"
        "Your FleetGo account has been created successfully.\n"
        "You can now browse available cars and manage rentals securely."
    ),
    "login_alert": (
        "Hello {customer_email},\n\n"
        "A successful login was detected on your FleetGo account.\n"
        "If this was not you, please contact support immediately."
    ),
    "rental_confirmed": (
        "Hello {customer_email},\n\n"
        "Your rental #{rental_id} for car #{car_id} has been confirmed.\n"
        "We look forward to serving you."
    ),
    "payment_received": (
        "Hello {customer_email},\n\n"
        "We received your {payment_kind} payment of {amount} "
        "for rental #{rental_id}.\n"
        "Thank you for choosing FleetGo."
    ),
}

SUBJECTS: dict[str, str] = {
    "welcome": "Welcome to FleetGo",
    "login_alert": "FleetGo login alert",
    "rental_confirmed": "Rental confirmed",
    "payment_received": "Payment received",
}


def send_customer_email(
    to_email: str,
    template: str,
    **context: Any,
) -> dict[str, Any]:
    """Render a standard email template and send it through SMTP."""
    if template not in TEMPLATES:
        raise ValueError(f"unsupported notification template: {template}")

    subject = SUBJECTS[template]
    body = TEMPLATES[template].format(customer_email=to_email, **context)
    return send_email(to_email=to_email, subject=subject, body=body)
