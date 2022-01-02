import asyncio
import csv
import re

import dateutil.parser
import requests

from .backup import Backup
from .employees import Employee, parse_employee_list, Employees
from .report import TimeClockReport
from .timeclock_preferences import Preferences


class TimeClockApi:
    TIMECLOCK_TIMESTAMP_EPOCH_DATE = dateutil.parser.parse("01/01/07")
    OT1_FACTOR = 1.5
    OT2_FACTOR = 2

    def __init__(self, timeclock_address, user, password):
        if timeclock_address.startswith("http"):
            self.address = timeclock_address
        else:
            self.address = "http://" + timeclock_address
        self.password = password
        self.username = user
        self.logged_in = False
        self._user_agent = "TimePass Python Client"
        self.session = requests.session()
        self._connect()
        self.employee_list: Employees = None
        self.preferences: Preferences = None
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__load_time_clock_data())
        loop.close()

    def _connect(self) -> None:
        endpoint = "login.html"
        login_payload = {
            "password": self.password,
            "username": self.username,
            "buttonClicked": "Submit",
        }
        res = self.make_request(endpoint, "POST", login_payload)

        res.raise_for_status()
        self.logged_in = True

    def get_preferences(self) -> Preferences:
        endpoint = "preferences.html"
        res = self.make_request(endpoint=endpoint)
        return Preferences.from_html(res.content)

    def make_request(
            self,
            endpoint,
            method: str = "GET",
            data=None,
            headers: dict = None,
            cookies: dict = None,
            json: dict = None,
            params: dict = None,
            **kwargs
    ) -> requests.Response:
        """
        simplifies creating requests as the base timeclock address can change. just specify the endpoint
        so you dont need to change it in a bunch of places
        :rtype requests.Response
        """
        url = "/".join([self.address, endpoint])
        if not headers:
            headers = {
                "User-Agent": self._user_agent,
            }
        if not cookies:
            cookies = self.session.cookies
        res = self.session.request(
            method,
            url,
            data=data,
            headers=headers,
            cookies=cookies,
            json=json,
            params=params,
            **kwargs,
        )
        res.raise_for_status()
        return res

    def get_timecard_export(self, from_date, to_date, emp_number=None) -> list[dict[str, str]]:
        """
        download a csv timecard report for the given dates and return a csv parsed list
        :param from_date:
        :param to_date:
        :param emp_number:
        :rtype: list of OrderedDict
        """

        from_date = dateutil.parser.parse(from_date)
        to_date = dateutil.parser.parse(to_date)
        from_timestamp = int(
            (from_date - self.TIMECLOCK_TIMESTAMP_EPOCH_DATE).total_seconds() / 60
        )
        to_timestamp = int(
            (to_date - self.TIMECLOCK_TIMESTAMP_EPOCH_DATE).total_seconds() / 60
        )

        if emp_number:
            emp_number = int(emp_number)
            emp_id = self.employee_list[emp_number].eid
        else:
            emp_id = 0
        default_report_page = "report.html?rt=2"
        export_endpoint = (
            "report.html?rt=2&"
            "type=7&"
            "from={from_date:%m/%d/%y}&to={to_date:%m/%d/%y}&eid=ss&export=1".format(
                from_date=from_date, to_date=to_date
            )
        )

        report_page_endpoint = (
            "report.html?rt=2&"
            "type=7?"
            "from={from_date:%m/%d/%y}&"
            "to={to_date:%m/%d/%y}&"
            "eid={id}".format(from_date=from_date, to_date=to_date, id=emp_id)
        )

        ajax_endpoint = "js/ajaxreport.html"

        ajax_payload = (
            "func=output2&"
            "reportType=2&"
            "intScopeFrom={}&"
            "intScopeTo={}&"
            "strSort=+strDisplayAs%2C+intEID%2C&"
            "showDepts=1&"
            "showFlags=1&"
            "scopeMenu=From%3A+{:%m%%2f%d%%2f%y}+Thru%3A+{:%m%%2f%d%%2f%y}&"
            "intEmployeeIDsel=0&"
            "blnUseMinutes=0&"
            "gUsePopupWindow=1&"
            "useBreak=1&blnIsCustom=0&"
            "reportFilter=filter_all_punches&"
            "ReportNonworkList=&"
            "ReportTimeRange1=&"
            "ReportTimeRange2=".format(from_timestamp, to_timestamp, from_date, to_date)
        )

        ajax_headers = {
            "Connection": "keep-alive",
            "Accept": "text/html, */*; q=0.01",
            "Origin": "http://" + self.address,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Python timepass scraper",
            "DNT": "1",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://" + self.address + "/" + report_page_endpoint,
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
        }
        # request ajaxhtml to for some reason allow queries later.
        ajax = self.make_request(
            ajax_endpoint, "POST", data=ajax_payload, headers=ajax_headers
        )
        # load original report page first
        self.make_request(default_report_page)

        # then load the target report page
        self.make_request(report_page_endpoint)

        headers = {
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Referer": "http://" + self.address + "/" + report_page_endpoint,
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
        }

        res = self.make_request(export_endpoint, headers=headers)
        report_data = res.content.decode("utf-8")
        reader = csv.DictReader(report_data.replace("\n", " ").split("\r"))
        report = [x for x in reader]
        return report

    def timeclock_report(self, from_date, to_date, emp_number=None):
        report_csv = self.get_timecard_export(from_date, to_date, emp_number)
        return TimeClockReport(report_csv)

    def get_employee_list(self, minimal: bool = True, active: bool = True) -> Employees:
        """
        get a list of all employees in the timeclock
        :param minimal: if true, only return the overview employee list
                        otherwise fetch each employee individually.
        :param active: if true, return active employees, else return inactive employees
        """
        endpoint = "employeelist.html"
        res = self.make_request(endpoint=endpoint, params={"active": int(active)})
        employees = parse_employee_list(res.content)
        if not minimal:
            for employee in employees:
                employee.get_details(self)
        return employees

    def get_employee(self, eid) -> Employee:
        ...

    def fetch_backup(self):
        """
        download a backup file from the time clock

        :return: filename, bytes
        """
        endpoint = "backup.html"
        payload = "buttonClicked=Submit&buttonClicked_2=none"
        headers = {
            "Referer": self.address + "/backup.html",
            "origin": self.address,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        backup = self.make_request(endpoint, "POST", data=payload, headers=headers)
        disposition = backup.headers["content-disposition"]
        filename = re.search('filename="(.*?)"', disposition).group(1)
        return Backup(filename=filename, data=backup.content)

    def export_employee_data(self):
        ...

    def export_employee_data_to_csv(self):
        ...

    # async function wrappers
    async def __as_get_employee_list(self):
        self.employee_list = self.get_employee_list()

    async def __as_get_preferences(self):
        self.preferences = self.get_preferences()

    async def __load_time_clock_data(self):
        """
        pull company configuration and employee list from the timeclock
        :return:
        """
        await asyncio.gather(self.__as_get_employee_list(), self.__as_get_preferences())

    async def __as_get_timecard_export(self, from_date, to_date, emp_number=None):
        return self.get_timecard_export(from_date, to_date, emp_number)
