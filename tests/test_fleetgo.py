# from datetime import UTC, datetime, timedelta

# from app.features.rentals.pricing import calculate_late_days
# from app.features.rentals.state_machine import ALLOWED_TRANSITIONS
# from app.models import RentalState


# def test_allowed_reserved_to_active():
#     assert (
#         RentalState.RESERVED,
#         RentalState.ACTIVE,
#     ) in ALLOWED_TRANSITIONS


# def test_allowed_active_to_returned():
#     assert (
#         RentalState.ACTIVE,
#         RentalState.RETURNED,
#     ) in ALLOWED_TRANSITIONS


# def test_allowed_reserved_to_cancelled():
#     assert (
#         RentalState.RESERVED,
#         RentalState.CANCELLED,
#     ) in ALLOWED_TRANSITIONS


# def test_disallowed_return_from_reserved():
#     allowed = {
#         (RentalState.RESERVED, RentalState.ACTIVE),
#         (RentalState.ACTIVE, RentalState.RETURNED),
#         (RentalState.RESERVED, RentalState.CANCELLED),
#     }

#     assert (
#         RentalState.RESERVED,
#         RentalState.RETURNED,
#     ) not in allowed


# def test_late_two_days():
#     end = datetime(
#         2026,
#         9,
#         10,
#         tzinfo=UTC,
#     )

#     returned = end + timedelta(days=2)

#     assert calculate_late_days(
#         end,
#         returned,
#     ) == 2


# def test_on_time_return_has_zero_late_days():

#     end = datetime(
#         2026,
#         9,
#         10,
#         tzinfo=UTC,
#     )

#     returned = end

#     assert calculate_late_days(
#         end,
#         returned,
#     ) == 0
