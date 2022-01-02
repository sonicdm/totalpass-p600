from dataclasses import dataclass, field
from datetime import date


@dataclass
class Accrual:
    name: str
    hours_available: float
    hours_used: float
    last_calculated_date: date
    yearly_hours: float = field(default=0)
    yearly_max_hours: float = field(default=0)
    reset_amount: float = field(default=0)
    allow_negative: bool = field(default=False)


class Accruals:
    def __init__(self, start_date: date, reset_date: date, accruals: list[Accrual]):
        self.start_date: date = start_date
        self.reset_date: date = reset_date
        self.accruals: list[Accrual] = accruals
        self.vacation: Accrual = None
        self.sick: Accrual = None
        self.personal: Accrual = None
        for accrual in accruals:
            setattr(self, accrual.name.lower(), accrual)
