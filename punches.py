import re
from datetime import datetime, date, timedelta

import dateutil.parser

from totalpass_p600.util import strings_to_numbers, date_to_datetime

PUNCH_TYPES = {
    0: "In",
    1: "Out",
    54: "Vacation",
    55: "Sick"
}


class Punches:
    """
    Catalog of employee punches
    Punches[employee_id] to retrieve all punches for an employee
    """

    def __init__(self):
        self.punches = []
        pass

    def add_punch(self, punch_record):
        """

        :param punch_record:
        :type punch_record: Punch or OrderedDict
        :return:
        """
        if isinstance(punch_record, Punch):
            self.punches.append(punch_record)
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

    def add_punches(self, report):
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

    def remove_punch(self, eid=None, visid=None, punchid=None):
        pass

    def punches_by_department(self, department):
        return self.punches_by_field("department", department.upper())

    def punches_by_field(self, field, value):
        punches = Punches()
        for punch in self.punches:
            if getattr(punch, field) == value:
                punches.add_punch(punch)
        return punches

    def punches_by_employee_id(self, visid):
        return self.punches_by_field("visible_id", visid)

    def punches_by_date(self, day):
        punches = Punches()
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
            range_punches.add_punches(p for p in self.punches_by_date(day).punches)
        return range_punches

    def punches_by_hour(self, hour, day=None):
        """
        given an hour return all standard punches for that hour.
        if day is specified only return that days punches
        """
        hours = {}
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


class Punch:
    OT1_FACTOR = 1.5
    OT2_FACTOR = 2

    def __init__(self, **kwargs):
        self.first_name = None
        self.middle_name = None
        self.last_name = None
        self.display_as = None
        self.address = None
        self.employee_id = None
        self.visible_id = None
        self.sort_date = None
        self.in_punch_id = None
        self.int_in_date = None
        self._in_date = None
        self.in_dow = None
        self._in_time = None
        self.in_flags = None
        self.in_punch_type = None
        self.in_note = None
        self.out_punch_id = None
        self.int_out_date = None
        self._out_date = None
        self.out_dow = None
        self._out_time = None
        self.out_flags = None
        self.out_punch_type = None
        self.out_note = None
        self.department = None
        self.lunch = None
        self.adj = None
        self.std = None
        self.ot1 = None
        self.ot2 = None
        self.wage = None
        self.int_calc_flags = None
        self.mot1 = None
        self.mot2 = None
        self.pin_number = None
        self.input = None

    def __repr__(self):
        in_str = "{in_time}".format(in_time=self.in_time)
        out_str = "{out_time}".format(out_time=self.out_time)
        if self.in_punch_type in (55, 54):
            return "<Punch {first}, {last}, Date: {in_date} {punch_type}, Total Hours: {total_hrs}>".format(
                first=self.first_name, last=self.last_name,
                in_date=self.in_date,
                punch_type=PUNCH_TYPES[self.in_punch_type],
                total_hrs=round(self.total_hours, 2)
            )

        return "<Punch {first}, {last}, In: {in_str}, Out: {out_str} Total Hours: {total_hrs}>".format(
            first=self.first_name, last=self.last_name,
            in_str=in_str, out_str=out_str,
            total_hrs=round(self.total_hours, 2)
        )

    def print_repr(self):
        return self.__repr__()

    @property
    def out_date(self):
        return dateutil.parser.parse(self._out_date).date()

    @property
    def in_date(self):
        return dateutil.parser.parse(self._in_date).date()

    @out_date.setter
    def out_date(self, day):
        if not day:
            self._out_date = self._in_date
        else:
            self._out_date = day

    @in_date.setter
    def in_date(self, day):
        self._in_date = day

    @property
    def in_time(self):
        return self._in_time

    @property
    def out_time(self):
        return self._out_time

    @in_time.setter
    def in_time(self, time):
        if not time:
            time = self._in_date
        else:
            time = dateutil.parser.parse(time)
        self._in_time = datetime(*self.in_date.timetuple()[:6]) + timedelta(hours=time.hour, minutes=time.minute,
                                                                            seconds=time.second)

    @out_time.setter
    def out_time(self, time):
        if not time:
            self._out_time = self._in_time
        else:
            time = dateutil.parser.parse(time)
            self._out_time = datetime(*self.out_date.timetuple()[:6]) + timedelta(hours=time.hour, minutes=time.minute,
                                                                                  seconds=time.second)

    @property
    def labor(self):
        ot1 = ((self.ot1 / 60) * self.wage) * self.OT1_FACTOR
        ot2 = ((self.ot2 / 60) * self.wage) * self.OT2_FACTOR
        std = (self.std / 60) * self.wage
        return ot1 + ot2 + std

    @property
    def total_hours(self):
        return (self.ot1 + self.ot2 + self.std) / 60

    def labor_by_hour(self, hour):
        hour_start = date_to_datetime(self.in_date, hour=hour)
        hour_end = date_to_datetime(self.in_date, hour=hour+1)
        hour_value = min((self.out_time, hour_end)).timestamp() - max((self.in_time, hour_start)).timestamp()
        if hour_value < 0:
            return 0
        punch_hours = hour_value / 60 / 60
        return punch_hours

    def labor_dollars_by_hour(self, hour):
        return self.labor_by_hour(hour) * self.wage


