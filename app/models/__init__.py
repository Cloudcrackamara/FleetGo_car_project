# Compatibility exports for the legacy test suite and app imports.
# The project expects direct imports such as `Car`, `User`, and `RentalState`.

from app.models.car import Car, CarClass, CarStatus
from app.models.payment import Payment, PaymentKind, PaymentMethod
from app.models.pricing import Pricing
from app.models.processed_event import ProcessedEvent
from app.models.rental import Rental, RentalState
from app.models.state_history import StateHistory
from app.models.user import User, UserRole
from app.models.workshop_visit import WorkshopVisit

Role = UserRole

__all__ = [
    "Car",
    "CarClass",
    "CarStatus",
    "Payment",
    "PaymentKind",
    "PaymentMethod",
    "Pricing",
    "ProcessedEvent",
    "Rental",
    "RentalState",
    "Role",
    "StateHistory",
    "User",
    "UserRole",
    "WorkshopVisit",
]