from __future__ import annotations

from datetime import date, timedelta


def count_travel_days(start_date: date, end_date: date, include_weekends: bool) -> int:
    if end_date < start_date:
        raise ValueError("end_date must not be before start_date")

    travel_days = 0
    current = start_date
    while current <= end_date:
        if include_weekends or current.weekday() < 5:
            travel_days += 1
        current += timedelta(days=1)
    return travel_days
