import os
from unittest import TestCase

from totalpass_p600.api import TimeClockApi
from totalpass_p600.employees import Employees


class TestTimeClockApi(TestCase):

    def test_fetch_backup(self):
        username = os.getenv("TIMECLOCK_USER")
        password = os.getenv("TIMECLOCK_PASS")
        address = "192.168.1.98"
        api = TimeClockApi("192.168.1.98", username, password)
        backup = api.fetch_backup()
        output_path = r'C:\temp\\' + backup.filename
        if os.path.exists(output_path):
            os.remove(output_path)
        backup.save(output_path)
        self.assertTrue(os.path.exists(output_path))

    def test_get_employee_list(self):
        username = os.getenv("TIMECLOCK_USER")
        password = os.getenv("TIMECLOCK_PASS")
        address = "192.168.1.98"
        api = TimeClockApi(address, username, password)
        employees = api.get_employee_list()
        self.assertTrue(len(employees) > 0)
        self.assertIsInstance(employees, Employees)
