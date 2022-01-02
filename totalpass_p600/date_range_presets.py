from datetime import date
from enum import Enum


def today() -> tuple[date, date]:
    t = date.today()
    return t, t


class DateRangePreset(Enum):
    """
    Enum for date range presets.
    """
    TODAY = 1
    THIS_WEEK = 2
    LAST_WEEK = 3
    LAST_PAY_PERIOD = 4
    THIS_PAY_PERIOD = 5
