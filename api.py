import csv
from urllib import parse

import dateutil.parser
import requests
from bs4 import BeautifulSoup

from totalpass_p600.employees import Employee
from utils import strings_to_numbers


class TimeClockApi(object):
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
        self._user_agent = "TimePass Python Client"
        self.session = requests.session()
        self._connect()
        self.employee_list = self.get_employee_list()
        pass

    def _connect(self):
        endpoint = "login.html"
        login_payload = {
            "password": self.password,
            "username": self.username,
            "buttonClicked": "Submit"
        }
        res = self.make_request(endpoint, "POST", login_payload)

        res.raise_for_status()

    def make_request(self, endpoint, method="GET", payload=None, headers=None, cookies=None, json=None, **kwargs):
        """
        simplifies creating requests as the base timeclock address can change. just specify the endpoint
        dont need to change it in a bunch of places
        :rtype requests.Response
        """
        url = "/".join([self.address, endpoint])
        if not headers:
            headers = {
                'User-Agent': self._user_agent,
            }
        if not cookies:
            cookies = self.session.cookies
        res = self.session.request(method, url, data=payload, headers=headers, cookies=cookies, json=json, **kwargs)
        res.raise_for_status()
        return res

    def get_timecard_export(self, from_date, to_date, emp_number=None):
        """
        download a csv timecard report for the given dates and return a csv parsed list
        :param from_date:
        :param to_date:
        :param emp_number:
        :rtype: list
        """

        from_date = dateutil.parser.parse(from_date)
        to_date = dateutil.parser.parse(to_date)
        from_timestamp = int((from_date - self.TIMECLOCK_TIMESTAMP_EPOCH_DATE).total_seconds() / 60)
        to_timestamp = int((to_date - self.TIMECLOCK_TIMESTAMP_EPOCH_DATE).total_seconds() / 60)

        if emp_number:
            emp_number = int(emp_number)
            emp_id = self.employee_list[emp_number].eid
        else:
            emp_id = 0
        default_report_page = "report.html?rt=2"
        export_endpoint = "report.html?rt=2&" \
                          "type=7&" \
                          "from={from_date:%m/%d/%y}&to={to_date:%m/%d/%y}&eid=ss&export=1".format(from_date=from_date,
                                                                                                   to_date=to_date
                                                                                                   )

        report_page_endpoint = 'report.html?rt=2&' \
                               'type=7?' \
                               'from={from_date:%m/%d/%y}&' \
                               'to={to_date:%m/%d/%y}&' \
                               'eid={id}'.format(from_date=from_date, to_date=to_date, id=emp_id)

        ajax_endpoint = "js/ajaxreport.html"

        ajax_payload = "func=output2&" \
                       "reportType=2&" \
                       "intScopeFrom={}&" \
                       "intScopeTo={}&" \
                       "strSort=+strDisplayAs%2C+intEID%2C&" \
                       "showDepts=1&" \
                       "showFlags=1&" \
                       "scopeMenu=From%3A+{:%m%%2f%d%%2f%y}+Thru%3A+{:%m%%2f%d%%2f%y}&" \
                       "intEmployeeIDsel=0&" \
                       "blnUseMinutes=0&" \
                       "gUsePopupWindow=1&" \
                       "useBreak=1&blnIsCustom=0&" \
                       "reportFilter=filter_all_punches&" \
                       "ReportNonworkList=&" \
                       "ReportTimeRange1=&" \
                       "ReportTimeRange2=".format(from_timestamp, to_timestamp, from_date, to_date)

        ajax_headers = {
            'Connection': 'keep-alive',
            'Accept': 'text/html, */*; q=0.01',
            'Origin': 'http://' + self.address,
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Python timepass scraper',
            'DNT': '1',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': "http://" + self.address + "/" + report_page_endpoint,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        # request ajaxhtml to for some reason allow queries later.
        ajax = self.make_request(ajax_endpoint, "POST", payload=ajax_payload, headers=ajax_headers)
        # load original report page first
        self.make_request(default_report_page)

        # then load the target report page
        self.make_request(report_page_endpoint)

        headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': "http://" + self.address + "/" + report_page_endpoint,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        res = self.make_request(export_endpoint, headers=headers)
        report_data = res.content.decode("utf-8")
        reader = csv.DictReader(report_data.replace("\n", " ").split("\r"))
        report = [x for x in reader]
        return report

    def get_employee_list(self):
        endpoint = "employeelist.html"
        employees = {}
        res = self.make_request(endpoint)
        employee_soup = BeautifulSoup(res.content, features="lxml")

        # get human readable values for item classes
        fieldmap = {}
        header_row = employee_soup.find("tr", {"class": "stalker-sort-bar"})
        for header in header_row.find_all("td"):
            fieldmap[str(header["class"][0])] = str(header.string)

        # find the list of employees
        employee_table = employee_soup.find("table", {"class": "cls_main_table"})

        for employee_row in employee_table.find_all("tr", {"class": None}):
            e = {}
            # scroll through td cells and assign values to the employee from the td class name
            for td in employee_row.find_all("td"):
                # if td has a link, use that opportunity to get the employees eid
                if td.a:
                    params = td.a['href']
                    # set the eid for the employee using urrllib to parse the query and find the eid
                    e["eid"] = int(parse.parse_qs(parse.urlsplit(params).query)["eid"][0])
                td_class = str(td['class'][0]).replace("cls_", "")
                e[td_class] = strings_to_numbers(str(td.string).title())

            # initialize employee object
            employee = Employee(e['fname'], e["mi"], e['lname'], e['visid'], e['eid'])
            employees[e["visid"]] = employee
        return employees