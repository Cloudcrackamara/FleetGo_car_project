
"""total = daily_rate * whole days booked. Late fee is computed
separately, at return time, by the state machine — not here, since
a late fee only exists once we know the ACTUAL return time, which
isn't known when the rental is first created."""

import math
from decimal import Decimal
from datetime import datetime

from app.models.rental import Rental


def compute_total(*, daily_rate: Decimal, start_at, end_at) -> Decimal:
    days = (end_at - start_at).days
    days = max(days, 1)  
    return daily_rate * days




def compute_late_fee(
    *, rental: Rental, actual_return_at: datetime, late_fee_per_day: Decimal
) -> Decimal:
    """A return exactly at end_at is on-time, not late — lateness only
    starts strictly after the deadline. Any part of a late day counts
    as a full day, consistent with compute_total's same-day-rental
    rule (days = max(days, 1))."""
    if actual_return_at <= rental.end_at:
        return Decimal("0")

    late_duration = actual_return_at - rental.end_at
    late_days = math.ceil(late_duration.total_seconds() / (24 * 60 * 60))
    return Decimal(late_days) * late_fee_per_day