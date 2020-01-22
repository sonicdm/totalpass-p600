from totalpass_p600.api import TimeClockApi
from totalpass_p600.punches import Punches


class TimeClockReport(TimeClockApi):

    def __init__(self, address, username, password, start, end, employee_id=None):
        super().__init__(address, username, password)
        self.raw_report = self.get_timecard_export(start, end, employee_id)
        self._punches = Punches()
        self.punches.add_punches(self.raw_report)
        self._assign_punches_to_employees()
        pass

    def pull_punches(self, report):
        for punch in report:
            if not any(v for v in punch.values()):
                continue
            # visid = punch["VisibleID"]
            self.punches.add_punch(punch)

    def _assign_punches_to_employees(self):
        for num, employee in self.employee_list.items():
            try:
                employee_punches = self.punches.punches_by_employee_id(num).punches
                if employee_punches:
                    employee.add_punches(employee_punches)
            except KeyError:
                pass

    @property
    def punches(self):
        return self._punches