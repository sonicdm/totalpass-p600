from __future__ import annotations

import re
from datetime import datetime, date, timedelta
from typing import Union, List

import dateutil.parser
from pydantic import BaseModel, Field, root_validator, validator

from .util import strings_to_numbers, date_to_datetime

PUNCH_TYPES = {
    0: "In",
    1: "Out",
    54: "Vacation",
    55: "Sick"
}


class Punches:
    """
    Collection of employee punches
    Punches[employee_id] to retrieve all punches for an employee
    """

    def __init__(self):
        self.punches = []
        self._days = set()
        pass

    def add_punch(self, punch_record):
        """

        :param punch_record:
        :type punch_record: Punch or OrderedDict
        :return:
        """
        if isinstance(punch_record, Punch):
            self.punches.append(punch_record)
            self._days.add(punch_record.in_date)
            return

        punch = Punch()
        if punch_record["FirstName"] == ' ':
            return
        for field, value in punch_record.items():
            subfield = re.sub(r"((?<=[a-z])[A-Z]|[A-Z](?=[a-z]))", r" \1", field)
            subfield = subfield.strip().replace(" ", "_").lower()
            setattr(punch, subfield, strings_to_numbers(value))
        if punch.in_date:
            self.punches.append(punch)
            self._days.add(punch.in_date)

    def add_punches(self, report: Union[Punches, List[Punch]]):
        if isinstance(report, Punches):
            for punch in report.punches:
                self.add_punch(punch)
            return

        for punch in report:
            # if not any(v for v in punch.values()):
            #     continue
            # # visid = punch["VisibleID"]
            self.add_punch(punch)

    def __getitem__(self, item):
        return self.punches_by_employee_id(item)

    def punches_by_department(self, department):
        return self.punches_by_field("department", department.upper())

    def departments(self):
        departments = {}
        for punch in self.punches:
            department = departments.setdefault(punch.department, Punches())
            department.add_punch(punch)
        return departments

    def punches_by_field(self, field, value):
        punches = Punches()
        for punch in self.punches:
            if getattr(punch, field) == value:
                punches.add_punch(punch)
        return punches

    def punches_by_employee_id(self, visid):
        return self.punches_by_field("visible_id", visid)

    def punches_by_date(self, day):
        # punches = Punches()
        if isinstance(day, datetime):
            day = day.date()
        elif not isinstance(day, (date, datetime)):
            day = dateutil.parser.parse(day).date()
        return self.punches_by_field("in_date", day)

    def punches_by_date_range(self, start, stop):
        range_punches = Punches()
        if not isinstance(start, (date, datetime)):
            start = dateutil.parser.parse(start).date()
        if not isinstance(stop, (date, datetime)):
            stop = dateutil.parser.parse(stop).date()
        days = (stop - start).days
        day_list = [start + timedelta(days=x) for x in range(days + 1)]
        for day in day_list:
            range_punches.add_punches([p for p in self.punches_by_date(day).punches])
        return range_punches

    def punches_by_hour(self, hour, day=None):
        """
        given an hour return all standard punches for that hour.
        if day is specified only return that days punches
        """
        # hours = {}
        hourly_punches = Punches()
        if day:
            punches = self.punches_by_date(day).punches
        else:
            punches = self.punches

        for punch in punches:
            if punch.in_punch_type in (55, 54):
                continue
            punch_hours = int((punch.out_time - punch.in_time).seconds / 60 / 60)
            punch_range = [punch.in_time + timedelta(hours=x) for x in range(punch_hours + 1)]
            if any(t.hour == hour for t in punch_range):
                hourly_punches.add_punch(punch)
        return hourly_punches

    def __iter__(self):
        return iter(self.punches)

    @property
    def total_labor(self):
        labor = 0
        for punch in self.punches:
            labor += punch.labor
        return labor

    @property
    def total_employees(self):
        ids = set()
        for punch in self.punches:
            ids.add(punch.visible_id)
        return len(ids)

    def days(self):
        days = {}
        for day in sorted(list(self._days)):
            days[day] = self.punches_by_date(day)
        return days


"""
timecards.csv headers:

FirstName,
MiddleName,
LastName,
DisplayAs,
Address,
EmployeeID,
VisibleID,
SortDate,
InPunchID,
intInDate,
InDate,
InDow,
InTime,
InFlags,
InPunchType,
InNote,
OutPunchID,
intOutDate,
OutDate,
OutDow,
OutTime,
OutFlags,
OutPunchType,
OutNote,
Department,
Lunch,
ADJ,STD,OT1,OT2, # clock values in minutes
Wage,
intCalcFlags,
MOT1,
MOT2,
PinNumber,
Input
"""


class Punch(BaseModel):
    """
    A punch record from the punch report. Loaded from timecards.csv
    """
    OT1_FACTOR = 1.5
    OT2_FACTOR = 2
    employee_id: str = Field(..., alias='EmployeeID')
    last_name: str = Field(..., alias='LastName')
    first_name: str = Field(..., alias='FirstName')
    middle_name: str = Field(..., alias='MiddleName')
    display_as: str = Field(..., alias='DisplayAs')
    address: str = Field(..., alias='Address')
    visible_id: str = Field(..., alias='VisibleID')
    sort_date: int = Field(..., alias='SortDate')
    in_punch_id: int = Field(..., alias='InPunchID')
    int_in_date: int = Field(..., alias='intInDate')
    in_date: date = Field(..., alias='InDate')  # MM/DD/YYYY
    in_dow: str = Field(..., alias='InDow')  # Mon, Tue, Wed, Thu, Fri, Sat, Sun
    in_time: datetime = Field(..., alias='InTime')  # HH:MM(a/p)
    in_flags: str = Field(..., alias='InFlags')
    in_punch_type: int = Field(..., alias='InPunchType')
    in_note: str = Field(..., alias='InNote')
    out_punch_id: int = Field(..., alias='OutPunchID')
    int_out_date: int = Field(..., alias='intOutDate')
    out_date: date = Field(..., alias='OutDate')  # MM/DD/YYYY
    out_dow: str = Field(..., alias='OutDow')  # Mon, Tue, Wed, Thu, Fri, Sat, Sun
    out_time: datetime = Field(..., alias='OutTime')  # HH:MM(a/p)
    out_flags: str = Field(..., alias='OutFlags')
    out_punch_type: int = Field(..., alias='OutPunchType')
    out_note: str = Field(..., alias='OutNote')
    department: str = Field(..., alias='Department')
    lunch: str = Field(..., alias='Lunch')
    # punch durations in minutes
    std: float = Field(..., alias='STD')
    adj: float = Field(..., alias='ADJ')
    ot1: float = Field(..., alias='OT1')
    ot2: float = Field(..., alias='OT2')
    wage: int = Field(..., alias='Wage')
    int_calc_flags: int = Field(..., alias='intCalcFlags')
    mot1: int = Field(..., alias='MOT1')
    mot2: int = Field(..., alias='MOT2')
    pin_number: int = Field(..., alias='PinNumber')
    inp: str = Field(..., alias='Input')

    @root_validator(pre=True)
    def punch_times_and_dates(cls, v):
        in_time = v.data['in_time']
        out_time = v.data['out_time']
        in_date = v.data['in_date']
        out_date = v.data['out_date']
        # convert dates to date object
        v.data['in_date'] = datetime.strptime(in_date, '%m/%d/%Y').date()
        v.data['out_date'] = datetime.strptime(out_date, '%m/%d/%Y').date()
        # convert times to datetime object on their respective dates
        v.data['in_time'] = datetime.combine(v.data['in_date'], in_time)
        v.data['out_time'] = datetime.combine(v.data['out_date'], out_time)
        return v

    # convert punch durations to hours from minutes
    @validator('std', 'adj', 'ot1', 'ot2')
    def convert_to_hours(cls, v) -> float:
        if v:
            return v / 60
        return 0.0

    def __repr__(self):
        # times in HH:MM(a/p) format with date in MM/DD/YYYY format
        in_str = f'{self.in_time.strftime("%m/%d/%Y")} {self.in_time.strftime("%I:%M%p")}'
        out_str = f'{self.out_time.strftime("%m/%d/%Y")} {self.out_time.strftime("%I:%M%p")}'
        if self.in_punch_type in (55, 54):  # punch is vacation or sick leave
            return f"<Punch {self.first_name}, {self.last_name}, Date: {self.in_date} " \
                   f"{PUNCH_TYPES[self.in_punch_type]}, Total Hours: {self.total_hours:.2f}>"

        else:  # punch is regular
            return f"<Punch {self.first_name}, {self.last_name}, In: {in_str}, Out: {out_str} " \
                   f"Total Hours: {self.total_hours:.2f}>"

    @property
    def labor(self) -> float:
        """
        Calculate the labor wages for this punch record.
        :return:
        """
        ot1 = (self.ot1 * self.wage) * self.OT1_FACTOR
        ot2 = (self.ot2 * self.wage) * self.OT2_FACTOR
        std = self.std * self.wage
        return sum([ot1, ot2, std])

    @property
    def total_hours(self) -> float:
        """
        Calculate the total hours for this punch record.
        :return:
        """
        return self.ot1 + self.ot2 + self.std

    def labor_by_hour(self, hour: int):
        """
        Calculate the labor hours for this punch record for a given hour.
        :param hour: hour in range 0-23 (0 is midnight)
        :return:
        """
        hour_start = date_to_datetime(self.in_date, hour=hour)
        hour_end = date_to_datetime(self.in_date, hour=hour + 1)
        punch_seconds = min((self.out_time, hour_end)).timestamp() - max((self.in_time, hour_start)).timestamp()
        if punch_seconds < 0:
            return 0
        punch_hours = punch_seconds / 60 / 60
        return punch_hours

    def labor_dollars_by_hour(self, hour):
        """
        Calculate the labor dollars for this punch record for a given hour.
        :param hour:
        :return:
        """
        return self.labor_by_hour(hour) * self.wage
