from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Union

from bs4 import BeautifulSoup
from dateutil.parser import parse as date_parser

from totalpass_p600.accrual import Accrual, Accruals
from totalpass_p600.web_punch import WebPunchSettings
from .punches import Punches

if TYPE_CHECKING:
    pass


@dataclass
class Employee:
    """An employee in the timeclock"""

    eid: int
    active: bool
    payroll_id: str
    display_id: str
    first_name: str
    middle_initial: str
    last_name: str
    display_name: str = field(default=None)
    pin: str = field(default=None)
    email: str = field(default="")
    address: str = field(default="")
    note: str = field(default="")
    entry_method: str = field(default="")
    automatic_lunch_deduction: bool = field(default=False)
    web_punch_settings: WebPunchSettings = field(default=None)
    accruals: Accruals = field(default_factory=dict)
    departments: dict[str, dict[str, Union[float, int]]] = field(
        default_factory=dict)  # departments and hourly wage assigned to them
    punches: Punches = field(default_factory=Punches)

    def __post_init__(self):
        if self.display_name is None:
            self.display_name = f"{self.first_name} {self.last_name}"

    def add_punch(self, punch_record):
        self.punches.add_punch(punch_record)

    def add_punches(self, punches):
        self.punches.add_punches(punches)

    @property
    def departments_list(self):
        return list(self.departments.keys())

    def __repr__(self):
        return f"Employee(eid={self.eid}, display_id={self.display_id}, " \
               f"fname={self.first_name}, lname={self.last_name}, departments={self.departments_list})"

    def __hash__(self):
        return hash(self.__repr__())


@dataclass
class Employees:
    """A collection of employees"""

    employees: dict[str, Employee] = field(default_factory=dict)

    def add_employee(self, employee: Employee) -> None:
        self.employees[employee.display_id] = employee

    def add_employees(self, employees) -> None:
        for employee in employees:
            self.add_employee(employee)

    def departments(self):
        departments = []
        for employee in self.employees.values():
            departments.extend(employee.departments_list)
        return set(departments)

    def by_department(self, department) -> Employees:
        emps = Employees()
        emps.add_employees(
            [
                employee
                for employee in self.employees.values()
                if department in employee.departments_list
            ]
        )
        return emps

    def __iter__(self):
        return iter(self.employees.values())

    def __getitem__(self, key):
        return self.employees[key]

    def __len__(self):
        return len(self.employees)

    def __hash__(self):
        return hash(tuple(self.employees.values()))


@dataclass
class EmployeeInformation:
    payroll_id: str
    first_name: str
    middle_initial: str
    last_name: str
    display_name: str
    address: str
    note: str
    email: str


def parse_employee_page(eid: int, page_html: str) -> Employee:
    """Parse the employee page and return an Employee object"""
    emp_soup = BeautifulSoup(page_html, "lxml")
    # get employee information
    payroll_id = emp_soup.select_one("#payrollID")["value"]
    display_id = emp_soup.select_one("#strVisibleID")["value"]
    pin = emp_soup.select_one("#pinb0").attrs["value"]
    first_name = emp_soup.select_one("#nameFirst")["value"]
    middle_initial = emp_soup.select_one("#initNameMiddle")["value"]
    last_name = emp_soup.select_one("#nameLast").attrs["value"]
    display_name = emp_soup.select_one("#nameDisplay")["value"]
    address = emp_soup.select_one("#strAddress").text
    note = emp_soup.select_one("#strNote").text
    email = emp_soup.select_one("#nameEmail")["value"]

    # get employee flags
    active = emp_soup.select_one("#blnActive").get("checked") == "checked"
    entry_method = (
        emp_soup.select_one("#entryMethod").find("option", {"selected": True}).text
    )
    automatic_lunch_deduction = (
        emp_soup.select_one("#lunchEnabFld").find("option", {"selected": True}).text
    )
    automatic_lunch_deduction = automatic_lunch_deduction == "Enabled"

    # get web punch settings
    assign_to_web_punch = (
            emp_soup.select_one("#wpAssignFld").get("checked") == "checked"
    )
    web_punch_password = emp_soup.select_one("#wpPasswordFld").get("value", "")
    authorized_web_punch_ip_addresses = emp_soup.select_one("#authorizedAddrFld").get(
        "value", ""
    )
    allow_unathorized_web_punch_ip_addresses = (
            emp_soup.select_one("#wpAllowUnauthIP").get("checked") == "checked"
    )
    use_global_web_punch_ip_addresses = (
            emp_soup.select_one("#wpUseGlobalIP").get("checked") == "checked"
    )
    web_punch_settings = WebPunchSettings(
        allowed=assign_to_web_punch,
        password=web_punch_password,
        authorized_ip_addresses=authorized_web_punch_ip_addresses,
        allow_punch_from_unauthorized_ip=allow_unathorized_web_punch_ip_addresses,
        use_global_authorized_ip_addresses=use_global_web_punch_ip_addresses,
    )
    # Get departments and wages
    department_soups = emp_soup.select(".deptsRow")
    depts = {}
    for dep_soup in department_soups:
        selected_dep = dep_soup.select_one(".deptsKey").find(
            "option", {"selected": True}
        )
        dep_id = int(selected_dep["value"])
        if dep_id < 1:
            continue
        dep_name = selected_dep.text
        wage = float(dep_soup.select_one(".deptsVal").input["value"])
        order = dep_soup.select_one(".deptsOrder")["value"]
        depts[dep_name] = {"wage": wage, "order": order}

    # get accruals
    accrual_trs = list(emp_soup.select_one("table.accrual").select('tr'))
    accrual_header = [th.text for th in accrual_trs[0].findAll('th')]
    accrual_list = []
    for accrual_tr in accrual_trs[1:]:
        accrual = {}
        for idx, td in enumerate(accrual_tr.findAll('td')):
            if td.text:
                accrual[accrual_header[idx]] = td.text
            elif td.input:
                if td.input['type'] == "text":
                    accrual[accrual_header[idx]] = td.input['value']
                if td.input['type'] == "checkbox":
                    accrual[accrual_header[idx]] = td.input.get('checked') == 'checked'
        accrual["LAST CALCULATED"] = date_parser(accrual["LAST CALCULATED"]).date()
        acc = Accrual(*accrual.values())
        accrual_list.append(acc)
    accrual_start_date = date_parser(emp_soup.select_one("#dteStartDate")['value']).date()
    accrual_reset_date = date_parser(emp_soup.select_one("#dteResetDate")['value']).date()
    accruals = Accruals(start_date=accrual_start_date, reset_date=accrual_reset_date, accruals=accrual_list)

    return Employee(
        eid=eid,
        payroll_id=payroll_id,
        display_id=display_id,
        pin=pin,
        first_name=first_name,
        middle_initial=middle_initial,
        last_name=last_name,
        display_name=display_name,
        address=address,
        note=note,
        email=email,
        active=active,
        entry_method=entry_method,
        automatic_lunch_deduction=automatic_lunch_deduction,
        web_punch_settings=web_punch_settings,
        departments=depts,
        accruals=accruals,
    )


def parse_employee_list(page_html) -> Employees:
    employee_soup = BeautifulSoup(page_html, "lxml")
    # get human readable values for item classes
    employees = Employees()
    # find the list of employees
    employee_table = employee_soup.select_one(".cls_main_table")
    table_body = employee_table.select_one('tbody')
    for employee_row in employee_table.find_all("tr", {"class": None}):
        active = employee_row.select_one(".cls_active").get("checked") is not None
        payroll_id = employee_row.select_one(".cls_payrollid").text
        visid = employee_row.select_one(".cls_visid").text
        last_name = employee_row.select_one(".cls_lname").text
        first_name = employee_row.select_one(".cls_fname").text
        middle_initial = employee_row.select_one(".cls_mi").text
        # web_punch = employee_row.select_one(".cls_wp").img is not None
        # daily_before_overtime = employee_row.select_one(".cls_daily").text
        # weekly_before_overtime = employee_row.select_one(".cls_weekly").text
        href = employee_row.select_one(".cls_payrollid").a.get("href")
        params = href.split("?")[1]
        params = {k: v for k, v in [param.split("=") for param in params.split("&")]}
        eid = int(params['eid'])
        employee = Employee(
            eid=eid,
            active=active,
            payroll_id=payroll_id,
            display_id=visid,
            first_name=first_name,
            middle_initial=middle_initial,
            last_name=last_name,
        )
        employees.add_employee(employee)
    return employees
