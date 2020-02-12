from unittest import TestCase
import os

from totalpass_p600.api import TimeClockApi


class TestTimeClockApi(TestCase):

    def test_fetch_backup(self):
        username = os.getenv("TIMECLOCK_USER")
        password = os.getenv("TIMECLOCK_PASS")
        address = "192.168.1.98"
        api = TimeClockApi("192.168.1.98", username, password)
        filename, backup_bytes = api.fetch_backup()
        output_path = r'C:\temp\\' + filename
        if os.path.exists(output_path):
            os.remove(output_path)
        with open(r'C:\temp\\' + filename, "wb") as f:
            f.write(backup_bytes)
