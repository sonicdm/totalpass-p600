from __future__ import annotations

from typing import List, TYPE_CHECKING

from .punches import Punches, Punch

if TYPE_CHECKING:
    from .api import TimeClockApi


class TimeClockReport:

    def __init__(self, raw_report: List[dict], api: TimeClockApi):
        self.api = api
        self.raw_report = raw_report
        self._punches = Punches()
        self.punches.add_punches()
        self._assign_punches_to_employees()
        pass

    def read_punches(self):
        for record in self.raw_report:
            if not any(v for v in record.values()):
                continue
            punch = Punch(**record)
            self.punches.add_punch(punch)

    def _assign_punches_to_employees(self):
        for num, employee in self.api.employee_list.items():
            try:
                employee_punches = self.punches.punches_by_employee_id(num).punches
                if employee_punches:
                    employee.add_punches(employee_punches)
            except KeyError:
                pass

    @property
    def punches(self):
        return self._punches
