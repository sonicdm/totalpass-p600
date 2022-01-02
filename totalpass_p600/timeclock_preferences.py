from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Union

from bs4 import Tag, BeautifulSoup
from pydantic import BaseModel, validator

# valid ip address regex from https://stackoverflow.com/a/166589
IP_ADDRESS_REGEX = re.compile(
    r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')


def str_to_time(v: str) -> time:
    """
    makes sure that the time is in the correct format of HH:MMa/p
    :param v:
    :return:
    """

    if isinstance(v, str):
        time_re = re.compile(r'^([0-1][0-9]|2[0-3]):([0-5][0-9])([pam]+)$')
        time_match = time_re.match(v)
        if time_re.match(v):
            am_pm = time_re.search(v).group(3)
            h = int(time_re.search(v).group(1))
            m = int(time_re.search(v).group(2))

            if am_pm.lower() in ['pm', 'p']:
                if h != 12:
                    h += 12
            elif am_pm.lower() in ['a', 'am'] and h == 12:
                h = 0
            return time(h, m)
        else:
            raise ValueError(f"{v} is not a valid time")
    return v


@dataclass
class CompanyInformation:
    """
    Company Name
    Company Payroll ID
    """
    company_name: str
    company_payroll_id: str

    @classmethod
    def from_soup(cls, form: Tag) -> CompanyInformation:
        # Company Information
        # Company Name selector #prefs2
        company_name = form.find("input", {"id": "prefs2"})["value"]
        # Company Payroll ID selector #prefs3
        company_payroll_id = form.find("input", {"id": "prefs3"})["value"]
        return cls(company_name, company_payroll_id)


class PayrollPreferences(BaseModel):
    """
    Pay Period Type
    Last Pay Start
    This Pay Start
    Next Pay Start
    Day Start
    Week Start: Sun, Mon, Tue, Wed, Thu, Fri, Sat
    """
    pay_period_type: str
    last_pay_start: date
    this_pay_start: date
    next_pay_start: date
    day_start: time
    week_start: str
    # Validators
    _validate_time = validator('day_start', pre=True, allow_reuse=True)(str_to_time)

    @validator('week_start')
    def validate_week_start(cls, v):
        if v.lower() not in ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']:
            raise ValueError(f'{v} is not a valid week start')
        return v.title()

    @validator('this_pay_start', 'next_pay_start', 'last_pay_start', pre=True)
    def validate_pay_dates(cls, v: str):
        """
        Validate the pay dates. from format 'MM/DD/YY'
        :param v:
        :return:
        """
        if isinstance(v, str):
            return datetime.strptime(v, '%m/%d/%y').date()
        return v

    @validator('pay_period_type')
    def validate_pay_period_type(cls, v: str):
        """
        Validate the pay period type. from format 'Weekly'
        :param v:
        :return:
        """
        if v.lower() not in ['weekly', 'bi-weekly', 'monthly', 'semi-monthly']:
            raise ValueError(f'{v} is not a valid pay period type')
        return v.title()

    @classmethod
    def from_soup(cls, form: Tag) -> PayrollPreferences:
        # Payroll Preferences
        # last pay start date selector #prefs9
        last_pay_start_date = form.find("input", {"id": "prefs9"})["value"]
        # this pay start date selector #prefs10
        this_pay_start_date = form.find("input", {"id": "prefs10"})["value"]
        # next pay start date selector #prefs11
        next_pay_start_date = form.find("input", {"id": "prefs11"})["value"]
        # pay period type dropdown selector #prefs5
        pay_period_type_dropdown = form.find("select", {"id": "prefs5"})
        pay_period_type = pay_period_type_dropdown.find("option", {"selected": "selected"}).text
        # Pay Period Start Date selector #prefs10 MM/DD/YY
        # Day Start selector #prefs13
        day_start = form.find("input", {"id": "prefs13"})["value"]
        # hour = int(day_start.split(':')[0])
        # minute = int(day_start.split(':')[1][:-1])
        # am_pm = day_start[-1]
        # if am_pm == 'p':
        #     hour += 12
        # day_start = time(hour, minute)
        # Week Start dropdown selector #prefs14
        week_start_dropdown = form.find("select", {"id": "prefs14"})
        week_start = week_start_dropdown.find("option", {"selected": "selected"}).text
        return cls(last_pay_start=last_pay_start_date, this_pay_start=this_pay_start_date,
                   next_pay_start=next_pay_start_date, pay_period_type=pay_period_type, day_start=day_start,
                   week_start=week_start)


class OvertimePreferences(BaseModel):
    """
    Day OT1 After x.xx Hours
    Day OT2 After x.xx Hours
    Week OT1 After x.xx Hours
    Week OT2 After x.xx Hours
    Consecutive Day OT: Yes/No
    OT1 Multiplier
    OT2 Multiplier
    """
    day_ot1_after_hours: float
    day_ot2_after_hours: float
    week_ot1_after_hours: float
    week_ot2_after_hours: float
    consecutive_day_ot: str  # Yes/No
    ot1_multiplier: float
    ot2_multiplier: float

    @validator('consecutive_day_ot', pre=True)
    def validate_consecutive_day_ot(cls, v: Union[str, bool]):
        if isinstance(v, str):
            if v.title() not in ['Yes', 'No']:
                raise ValueError(f'{v} is not a valid consecutive day ot value')
            return v.title()
        elif isinstance(v, bool):
            return 'Yes' if v else 'No'

    @classmethod
    def from_soup(cls, form: Tag) -> OvertimePreferences:
        # Overtime Preferences
        # Day Overtime 1 selector #prefs17
        day_overtime_1 = form.find("input", {"id": "prefs17"})["value"]
        # Day Overtime 2 selector #prefs18
        day_overtime_2 = form.find("input", {"id": "prefs18"})["value"]
        # Week Overtime 1 selector #prefs19
        week_overtime_1 = form.find("input", {"id": "prefs19"})["value"]
        # Week Overtime 2 selector #prefs20
        week_overtime_2 = form.find("input", {"id": "prefs20"})["value"]
        # Consecutive Day Overtime dropdown selector #prefs21 Yes/No
        consecutive_day_overtime_dropdown = form.find("select", {"id": "prefs21"})
        consecutive_day_overtime = consecutive_day_overtime_dropdown.find("option", {"selected": "selected"}).text
        # OT1 Multiplier selector #prefs25
        ot1_multiplier = form.find("input", {"id": "prefs25"})["value"]
        # OT2 Multiplier selector #prefs26
        ot2_multiplier = form.find("input", {"id": "prefs26"})["value"]
        return cls(day_ot1_after_hours=day_overtime_1, day_ot2_after_hours=day_overtime_2,
                   week_ot1_after_hours=week_overtime_1, week_ot2_after_hours=week_overtime_2,
                   consecutive_day_ot=consecutive_day_overtime, ot1_multiplier=ot1_multiplier,
                   ot2_multiplier=ot2_multiplier)


class PunchPreferences(BaseModel):
    """
    fields:
    Rounding Type: None, 15 Minute, 15 Minute slant, 10th hour
    Automatic Punches become IN at x.xx hours
    Flag edits on reports: bool
    Reject Like Punches within x minutes of each other
    Global Authorized Web Punch  Address(es) comma separated
    """
    rounding_type: str
    auto_punch_in_after_hours: float
    flag_edits_on_reports: bool
    reject_like_punches_range: int  # time in minutes to ignore similar punches
    global_authorized_web_punch_addresses: list[str]

    # Validators
    @validator('rounding_type', pre=True)
    def validate_rounding_type(cls, v: str):
        if v.lower() not in ['none', '15 minute', '15 minute slant', '10th hour']:
            raise ValueError(f'{v} is not a valid rounding type')
        return v.lower()

    @validator('global_authorized_web_punch_addresses', pre=True)
    def validate_ip_addresses(cls, v: str) -> list[str]:
        """
        Split comma separated ip addresses into a list of strings
        validate that each ip address is a valid ip address or domain
        """
        ip_addresses = v.split(',')
        for ip_address in ip_addresses:
            if not IP_ADDRESS_REGEX.match(ip_address.strip()):
                raise ValueError(f'{ip_address} is not a valid ip address')
        return ip_addresses

    @classmethod
    def from_soup(cls, form: Tag) -> PunchPreferences:
        # Punch Preferences
        # rounding type dropdown selector #prefs30
        rounding_type_dropdown = form.find("select", {"id": "prefs30"})
        rounding_type = rounding_type_dropdown.find("option", {"selected": "selected"}).text
        # Automatic Punches become IN at x.xx hours selector #prefs31
        auto_punch_in_after_hours = form.find("input", {"id": "prefs31"})["value"]
        # Flag edits on reports selector #prefs32
        flag_edits_on_reports = form.find("input", {"id": "prefs32"}).get("checked") is not None
        # Reject Like Punches within x minutes of each other selector #prefs33
        reject_like_punches_range = form.find("input", {"id": "prefs33"})["value"]
        # Global Authorized Web Punch  Address(es) comma separated selector #prefs70
        global_authorized_web_punch_addresses = form.find("input", {"id": "prefs70"})["value"]
        return cls(rounding_type=rounding_type, auto_punch_in_after_hours=auto_punch_in_after_hours,
                   flag_edits_on_reports=flag_edits_on_reports, reject_like_punches_range=reject_like_punches_range,
                   global_authorized_web_punch_addresses=global_authorized_web_punch_addresses)


@dataclass
class HiddenInputs:
    def __init__(self, form: Tag):
        self.form = form
        self.hidden_inputs_tags = self.form.find_all('input', {'type': 'hidden'})
        self.hidden_inputs = self.__get_hidden_inputs()

    def __get_hidden_inputs(self):
        return {tag['name']: tag['value'] for tag in self.hidden_inputs_tags}

    def __get_hidden_input(self, name: str):
        return self.hidden_inputs[name]

    def __set_hidden_input(self, name: str, value: str):
        self.hidden_inputs[name] = value


@dataclass
class EmployeeInputPreferences:
    """
    fields:
    enabled: bool
    Input Name
    Collection Type: Currency, Number
    Collect On: OUT, IN
    Show Totals: bool
    """
    enabled: bool
    input_name: str
    collection_type: str
    collect_on: str
    show_totals: bool

    # Validators
    @validator('collection_type')
    def validate_collection_type(self, v: str) -> str:
        if v.lower() not in ['currency', 'number']:
            raise ValueError(f'{v} is not a valid collection type')
        return v.title()

    @validator('collect_on')
    def validate_collect_on(self, v: str) -> str:
        if v.upper() not in ['OUT', 'IN']:
            raise ValueError(f'{v} is not a valid collect on')
        return v.upper()

    @classmethod
    def from_soup(cls, form: Tag) -> EmployeeInputPreferences:
        # Employee Input Preferences
        # enabled drown down selector #prefs36
        enabled_dropdown = form.find("select", {"id": "prefs36"})
        enabled = enabled_dropdown.find("option", {"selected": "selected"})["value"] == "selected"
        # Input Name selector #prefs37
        input_name = form.find("input", {"id": "prefs37"})["value"]
        # Collection Type dropdown selector #prefs38
        collection_type_dropdown = form.find("select", {"id": "prefs38"})
        collection_type = collection_type_dropdown.find("option", {"selected": "selected"}).text
        # Collect On dropdown selector #prefs39
        collect_on_dropdown = form.find("select", {"id": "prefs39"})
        collect_on = collect_on_dropdown.find("option", {"selected": "selected"}).text
        # Show Totals checkbox #prefs40
        show_totals = form.find("input", {"id": "prefs40"}).get("checked") is not None
        return cls(enabled=enabled, input_name=input_name, collection_type=collection_type, collect_on=collect_on,
                   show_totals=show_totals)


@dataclass
class DeviceInformation:
    """
    fields:
    Database Version:1510191
    Software Version:8790
    Serial Number:T002-060-549
    """
    database_version: str
    software_version: str
    serial_number: str

    @classmethod
    def from_soup(cls, form: Tag) -> DeviceInformation:
        # Device Information
        # Database Version div #prefsDiv42
        database_version_div = form.find("div", {"id": "prefsDiv42"})
        database_version = database_version_div.select_one(".prefsVal").text.strip()
        # Software Version div #prefsDiv43
        software_version_div = form.find("div", {"id": "prefsDiv43"})
        software_version = software_version_div.select_one(".prefsVal").text.strip()
        # Serial Number div #prefsDiv44
        serial_number_div = form.find("div", {"id": "prefsDiv44"})
        serial_number = serial_number_div.select_one(".prefsVal").text.strip()
        return cls(database_version=database_version, software_version=software_version, serial_number=serial_number)


@dataclass
class DevicePreferences:
    """
    Calculated Time Format: Hundredths/Minutes
    PIN Number Length: int
    Hide Employee PIN: bool
    System Prompt 1:str # Enter Emp #
    System Prompt 2:str # Enter Emp #
    System Prompt 3 str # Enter Emp #
    Supervisor Code: str
    Lock Keypad: bool
    Use Daylight Savings: bool
    Default Attendance Report To: Today, Yesterday, Last Week, This Week, Last Pay, This Pay
    Default Timecard Report To: Today, Yesterday, Last Week, This Week, Last Pay, This Pay
    Refresh Home Page Every x Minutes: int
    Use SSL Server: bool
    Use Popup Windows for Edits: Yes, No, Yes with Batch Edits
    Show total hours at the clock: bool
    """
    calculated_time_format: str
    pin_number_length: int
    hide_employee_pin: bool
    system_prompt_1: str
    system_prompt_2: str
    system_prompt_3: str
    supervisor_code: str
    lock_keypad: bool
    use_daylight_savings: bool
    default_attendance_report_to: str
    default_timecard_report_to: str
    refresh_home_page_every_x_minutes: int
    use_ssl_server: bool
    use_popup_windows_for_edits: str
    show_total_hours_at_the_clock: bool

    # Validators
    @validator('calculated_time_format')
    def validate_calculated_time_format(self, v: str) -> str:
        if v.title() not in ['Hundredths', 'Minutes']:
            raise ValueError(f'{v} is not a valid calculated time format')
        return v.title()

    @validator('default_attendance_report_to', 'default_timecard_report_to')
    def validate_default_report_to(self, v: str) -> str:
        if v.title() not in ['Today', 'Yesterday', 'Last Week', 'This Week', 'Last Pay', 'This Pay']:
            raise ValueError(f'{v} is not a valid default report to')
        return v.title()

    @validator('use_popup_windows_for_edits')
    def validate_use_popup_windows_for_edits(self, v: str) -> str:
        if v.title() not in ['Yes', 'No', 'Yes With Batch Edits']:
            raise ValueError(f'{v} is not a valid use popup windows for edits')
        return v.title()

    @classmethod
    def from_soup(cls, form: Tag) -> DevicePreferences:
        # Device Preferences
        # Calculated Time Format dropdown selector #prefs47
        calculated_time_format_dropdown = form.find("select", {"id": "prefs47"})
        calculated_time_format = calculated_time_format_dropdown.find("option", {"selected": "selected"}).text
        # PIN Number Length dropdown #prefs48
        pin_number_length_dropdown = form.find("select", {"id": "prefs48"})
        pin_number_length = int(pin_number_length_dropdown.find("option", {"selected": "selected"}).text)

        # Hide Employee PIN checkbox #prefs49
        hide_employee_pin_checkbox = form.find("input", {"id": "prefs49"})
        hide_employee_pin = hide_employee_pin_checkbox.get("checked") is not None
        # System Prompt 1 input #prefs50
        system_prompt_1 = form.find("input", {"id": "prefs50"})["value"]
        # System Prompt 2 input #prefs51
        system_prompt_2 = form.find("input", {"id": "prefs51"})["value"]
        # System Prompt 3 input #prefs52
        system_prompt_3 = form.find("input", {"id": "prefs52"})["value"]
        # Supervisor Code input #prefs53
        supervisor_code = form.find("input", {"id": "prefs53"})["value"]
        # Lock Keypad checkbox #prefs54
        lock_keypad = form.find("input", {"id": "prefs54"}).get("checked") is not None
        # Use Daylight Savings checkbox #prefs55
        use_daylight_savings = form.find("input", {"id": "prefs55"}).get("checked") is not None
        # Default Attendance Report To dropdown selector #prefs56
        default_attendance_report_to_dropdown = form.find("select", {"id": "prefs56"})
        default_attendance_report_to = default_attendance_report_to_dropdown.find(
            "option", {"selected": "selected"}).text
        # Default Timecard Report To dropdown selector #prefs57
        default_timecard_report_to_dropdown = form.find("select", {"id": "prefs57"})
        default_timecard_report_to = default_timecard_report_to_dropdown.find("option", {"selected": "selected"}).text
        # Refresh Home Page Every x Minutes input #prefs58
        refresh_home_page_every_x_minutes = int(form.find("input", {"id": "prefs58"})["value"])
        # Use SSL Server checkbox #prefs59
        use_ssl_server = form.find("input", {"id": "prefs59"}).get("checked") is not None
        # Use Popup Windows for Edits dropdown #prefs60
        use_popup_windows_for_edits_dropdown = form.find("select", {"id": "prefs60"})
        use_popup_windows_for_edits = use_popup_windows_for_edits_dropdown.find("option", {"selected": "selected"}).text

        # Show total hours at the clock checkbox #prefs61
        show_total_hours_at_the_clock = form.find("input", {"id": "prefs61"}).get("checked") is not None

        return cls(
            calculated_time_format=calculated_time_format,
            pin_number_length=pin_number_length,
            hide_employee_pin=hide_employee_pin,
            system_prompt_1=system_prompt_1,
            system_prompt_2=system_prompt_2,
            system_prompt_3=system_prompt_3,
            supervisor_code=supervisor_code,
            lock_keypad=lock_keypad,
            use_daylight_savings=use_daylight_savings,
            default_attendance_report_to=default_attendance_report_to,
            default_timecard_report_to=default_timecard_report_to,
            refresh_home_page_every_x_minutes=refresh_home_page_every_x_minutes,
            use_ssl_server=use_ssl_server,
            use_popup_windows_for_edits=use_popup_windows_for_edits,
            show_total_hours_at_the_clock=show_total_hours_at_the_clock
        )


# MULTI-CLOCK PREFERENCES
@dataclass
class MultiClockPreferences:
    """
    Child realtime Time/Date sync: bool
    Child realtime data sync: bool
    Child Online sync delay x seconds: int
    Child Offline sync delay x seconds: int
    """
    child_realtime_time_date_sync: bool
    child_realtime_data_sync: bool
    child_online_sync_delay_seconds: int
    child_offline_sync_delay_seconds: int

    @classmethod
    def from_soup(cls, form: Tag) -> MultiClockPreferences:
        # Child realtime Time/Date sync checkbox #prefs64
        child_realtime_time_date_sync = form.find("input", {"id": "prefs64"}).get("checked") is not None
        # Child realtime data sync checkbox #prefs65
        child_realtime_data_sync = form.find("input", {"id": "prefs65"}).get("checked") is not None
        # Child Online sync delay x seconds input #prefs66
        child_online_sync_delay_x_seconds = int(form.find("input", {"id": "prefs66"})["value"])
        # Child Offline sync delay x seconds input #prefs67
        child_offline_sync_delay_x_seconds = int(form.find("input", {"id": "prefs67"})["value"])

        return cls(child_realtime_data_sync=child_realtime_data_sync,
                   child_realtime_time_date_sync=child_realtime_time_date_sync,
                   child_online_sync_delay_seconds=child_online_sync_delay_x_seconds,
                   child_offline_sync_delay_seconds=child_offline_sync_delay_x_seconds)


#  EMAIL/SMTP PREFERENCES
class EmailPreferences(BaseModel):
    """
    fields:
    SMTP Server Address: 192.168.1.167
    Use SSL: bool
    Use STARTTLS: bool
    Use Authentication: bool
    Username/Email Address: str
    Password: str
    From Email Address: str
    Email Domain Name: str
    Email Backups To: str
    Send Backups: Daily, Weekly, Monthly
    """
    smtp_server_address: str
    use_ssl: bool
    use_starttls: bool
    use_authentication: bool
    username_email_address: str
    password: str
    from_email_address: str
    email_domain_name: str
    email_backups_to: str
    send_backups: str

    @validator('send_backups')
    def send_backups_validator(cls, send_backups):
        if send_backups.title() not in ['Daily', 'Weekly', 'Monthly']:
            raise ValueError('send_backups must be Daily, Weekly, or Monthly')
        return send_backups.title()

    @classmethod
    def from_soup(cls, form: Tag) -> EmailPreferences:
        # SMTP Server Address input #prefs73
        smtp_server_address = form.find("input", {"id": "prefs73"})["value"]
        # Use SSL checkbox #prefs74
        use_ssl = form.find("input", {"id": "prefs74"}).get("checked") is not None
        # Use STARTTLS checkbox #prefs75
        use_starttls = form.find("input", {"id": "prefs75"}).get("checked") is not None
        # Use Authentication checkbox #prefs76
        use_authentication = form.find("input", {"id": "prefs76"}).get("checked") is not None
        # Username/Email Address input #prefs77
        username_email_address = form.find("input", {"id": "prefs77"})["value"]
        # Password input #prefs78
        password = form.find("input", {"id": "prefs78"})["value"]
        # From Email Address input #prefs79
        from_email_address = form.find("input", {"id": "prefs79"})["value"]
        # Email Domain Name input #prefs80
        email_domain_name = form.find("input", {"id": "prefs80"})["value"]
        # Email Backups To input #prefs81
        email_backups_to = form.find("input", {"id": "prefs81"})["value"]
        # Send Backups dropdown #prefs82
        send_backups_dropdown = form.find("select", {"id": "prefs82"})
        send_backups = send_backups_dropdown.find("option", {"selected": "selected"}).text

        return cls(smtp_server_address=smtp_server_address, use_ssl=use_ssl, use_starttls=use_starttls,
                   use_authentication=use_authentication, username_email_address=username_email_address,
                   password=password, from_email_address=from_email_address, email_domain_name=email_domain_name,
                   email_backups_to=email_backups_to, send_backups=send_backups)


# ALERT PREFERENCES
class AlertPreferences(BaseModel):
    """
    Alert Low Hours at x.xx Hours per punch
    Alert High Hours at x.xx Hours per punch
    Maximum Punch Time at x.xx Hours per punch
    Alert Day Overtime OT at x.xx Hours remaining
    Alert Week Overtime OT at x.xx Hours remaining
    Check Alerts Every x Minutes
    Email Alerts Every x Minutes
    Update Employee Hours Every x Minutes
    Email Daily Alerts at mm:hh(a/p)
    """
    alert_low_hours_threshold: float
    alert_high_hours_threshold: float
    maximum_punch_time_threshold: float
    day_overtime_threshold: float
    week_overtime_threshold: float
    check_alerts_interval: int
    email_alerts_interval: int
    update_employee_hours_interval: int
    email_daily_alerts_time: str

    # Validators
    _validate_time = validator('email_daily_alerts_time', allow_reuse=True)(str_to_time)

    @classmethod
    def from_soup(cls, form: Tag) -> AlertPreferences:
        # Alert Low Hours at x.xx Hours per punch #prefs86
        alert_low_hours_threshold = float(form.find("input", {"id": "prefs86"})["value"])
        # Alert High Hours at x.xx Hours per punch #prefs87
        alert_high_hours_threshold = float(form.find("input", {"id": "prefs87"})["value"])
        # Maximum Punch Time at x.xx Hours per punch #prefs88
        maximum_punch_time_threshold = float(form.find("input", {"id": "prefs88"})["value"])
        # Alert Day Overtime OT at x.xx Hours remaining #prefs89
        alert_day_overtime_ot_threshold = float(form.find("input", {"id": "prefs89"})["value"])
        # Alert Week Overtime OT at x.xx Hours remaining #prefs90
        alert_week_overtime_ot_threshold = float(form.find("input", {"id": "prefs90"})["value"])
        # Check Alerts Every x Minutes #prefs92
        check_alerts_interval = int(form.find("input", {"id": "prefs92"})["value"])
        # Email Alerts Every x Minutes #prefs93
        email_alerts_interval = int(form.find("input", {"id": "prefs93"})["value"])
        # Update Employee Hours Every x Minutes #prefs94
        update_employee_hours_interval = int(form.find("input", {"id": "prefs94"})["value"])
        # Email Daily Alerts at mm:hh(a/p) #prefs95
        email_daily_alerts_time = form.find("input", {"id": "prefs95"})["value"]

        return cls(alert_low_hours_threshold=alert_low_hours_threshold,
                   alert_high_hours_threshold=alert_high_hours_threshold,
                   maximum_punch_time_threshold=maximum_punch_time_threshold,
                   day_overtime_threshold=alert_day_overtime_ot_threshold,
                   week_overtime_threshold=alert_week_overtime_ot_threshold,
                   check_alerts_interval=check_alerts_interval,
                   email_alerts_interval=email_alerts_interval,
                   update_employee_hours_interval=update_employee_hours_interval,
                   email_daily_alerts_time=email_daily_alerts_time)


class CustomField(BaseModel):
    """
    Name for Field
    Assign Field to: None, System, Employee, Department
    """
    name: str
    assign: str

    @validator('assign')
    def validate_assign(cls, v):
        if v not in ['None', 'System', 'Employee', 'Department']:
            raise ValueError('Assign must be one of None, System, Employee, Department')
        return v


class CustomFieldPreferences(BaseModel):
    """
    10 Fields
    Title for Field
    Assign Field to: None, System, Employee, Department
    """
    field_1: CustomField
    field_2: CustomField
    field_3: CustomField
    field_4: CustomField
    field_5: CustomField
    field_6: CustomField
    field_7: CustomField
    field_8: CustomField
    field_9: CustomField
    field_10: CustomField

    class Config:
        use_arbitrary_types = True

    @classmethod
    def from_soup(cls, form: Tag) -> CustomFieldPreferences:
        # field 1 name #prefs100
        # field 1 assign dropdown #prefs101
        field_1_dropdown = form.find("select", {"id": "prefs101"})
        field_1_assign_to = field_1_dropdown.find("option", {"selected": "selected"}).text
        custom_field_1 = CustomField(name=form.find("input", {"id": "prefs100"})["value"], assign=field_1_assign_to)

        # field 2 name #prefs103
        # field 2 assign dropdown #prefs104
        field_2_dropdown = form.find("select", {"id": "prefs104"})
        field_2_assign_to = field_2_dropdown.find("option", {"selected": "selected"}).text
        custom_field_2 = CustomField(name=form.find("input", {"id": "prefs103"})["value"], assign=field_2_assign_to)

        # field 3 name #prefs106
        # field 3 assign dropdown #prefs107
        field_3_dropdown = form.find("select", {"id": "prefs107"})
        field_3_assign_to = field_3_dropdown.find("option", {"selected": "selected"}).text
        custom_field_3 = CustomField(name=form.find("input", {"id": "prefs106"})["value"], assign=field_3_assign_to)

        # field 4 name #prefs109
        # field 4 assign dropdown #prefs110
        field_4_dropdown = form.find("select", {"id": "prefs110"})
        field_4_assign_to = field_4_dropdown.find("option", {"selected": "selected"}).text
        custom_field_4 = CustomField(name=form.find("input", {"id": "prefs109"})["value"], assign=field_4_assign_to)

        # field 5 name #prefs112
        # field 5 assign dropdown #prefs113
        field_5_dropdown = form.find("select", {"id": "prefs113"})
        field_5_assign_to = field_5_dropdown.find("option", {"selected": "selected"}).text
        custom_field_5 = CustomField(name=form.find("input", {"id": "prefs112"})["value"], assign=field_5_assign_to)

        # field 6 name #prefs115
        # field 6 assign dropdown #prefs116
        field_6_dropdown = form.find("select", {"id": "prefs116"})
        field_6_assign_to = field_6_dropdown.find("option", {"selected": "selected"}).text
        custom_field_6 = CustomField(name=form.find("input", {"id": "prefs115"})["value"], assign=field_6_assign_to)

        # field 7 name #prefs118
        # field 7 assign dropdown #prefs119
        field_7_dropdown = form.find("select", {"id": "prefs119"})
        field_7_assign_to = field_7_dropdown.find("option", {"selected": "selected"}).text
        custom_field_7 = CustomField(name=form.find("input", {"id": "prefs118"})["value"], assign=field_7_assign_to)

        # field 8 name #prefs121
        # field 8 assign dropdown #prefs122
        field_8_dropdown = form.find("select", {"id": "prefs122"})
        field_8_assign_to = field_8_dropdown.find("option", {"selected": "selected"}).text
        custom_field_8 = CustomField(name=form.find("input", {"id": "prefs121"})["value"], assign=field_8_assign_to)
        # field 9 name #prefs124
        # field 9 assign dropdown #prefs125
        field_9_dropdown = form.find("select", {"id": "prefs125"})
        field_9_assign_to = field_9_dropdown.find("option", {"selected": "selected"}).text
        custom_field_9 = CustomField(name=form.find("input", {"id": "prefs124"})["value"], assign=field_9_assign_to)

        # field 10 name #prefs127
        # field 10 assign dropdown #prefs128
        field_10_dropdown = form.find("select", {"id": "prefs128"})
        field_10_assign_to = field_10_dropdown.find("option", {"selected": "selected"}).text
        custom_field_10 = CustomField(name=form.find("input", {"id": "prefs127"})["value"], assign=field_10_assign_to)

        return cls(field_1=custom_field_1, field_2=custom_field_2, field_3=custom_field_3, field_4=custom_field_4,
                   field_5=custom_field_5, field_6=custom_field_6, field_7=custom_field_7, field_8=custom_field_8,
                   field_9=custom_field_9, field_10=custom_field_10)


class PreferenceForm:
    def __init__(self, form: Tag):
        self.id = form['id']
        self.form = form  # form tag
        self.name = form.get('name')
        self.action = form.get('action')
        self.method = form.get('method')
        self.hidden_inputs = HiddenInputs(form)

        self.hidden_inputs = HiddenInputs(form)


@dataclass
class Preferences:
    """
    Preferences:
    collection of preference objects
    """
    company_information: CompanyInformation
    payroll_preferences: PayrollPreferences
    overtime_preferences: OvertimePreferences
    punch_preferences: PunchPreferences
    employee_input_preferences: EmployeeInputPreferences
    device_information: DeviceInformation
    device_preferences: DevicePreferences
    multi_clock_preferences: MultiClockPreferences
    custom_field_preferences: CustomFieldPreferences
    email_preferences: EmailPreferences
    preferences_form: PreferenceForm
    alert_preferences: AlertPreferences

    @classmethod
    def from_soup(cls, soup: BeautifulSoup) -> Preferences:
        """
        :param soup:
        :return:
        """
        form = soup.find("form", {"id": "formMain"})
        company_information = CompanyInformation.from_soup(form)
        payroll_preferences = PayrollPreferences.from_soup(form)
        overtime_preferences = OvertimePreferences.from_soup(form)
        punch_preferences = PunchPreferences.from_soup(form)
        employee_input_preferences = EmployeeInputPreferences.from_soup(form)
        device_information = DeviceInformation.from_soup(form)
        device_preferences = DevicePreferences.from_soup(form)
        multi_clock_preferences = MultiClockPreferences.from_soup(form)
        custom_field_preferences = CustomFieldPreferences.from_soup(form)
        email_preferences = EmailPreferences.from_soup(soup)
        alert_preferences = AlertPreferences.from_soup(soup)
        preferences_form = PreferenceForm(form)
        return cls(
            company_information=company_information,
            payroll_preferences=payroll_preferences,
            overtime_preferences=overtime_preferences,
            punch_preferences=punch_preferences,
            employee_input_preferences=employee_input_preferences,
            device_information=device_information,
            device_preferences=device_preferences,
            multi_clock_preferences=multi_clock_preferences,
            email_preferences=email_preferences,
            alert_preferences=alert_preferences,
            custom_field_preferences=custom_field_preferences,
            preferences_form=preferences_form,
        )

    @classmethod
    def from_html(cls, html: str) -> Preferences:
        """
        :param html:
        :return:
        """
        soup = BeautifulSoup(html, 'html.parser')
        return cls.from_soup(soup)


###############################################################################
# html parsing for preferences pages                                          #
###############################################################################

preference_div_names = {
    0: "pay",
    1: "punch",
    2: "device",
    3: "alerts",
    4: "custom fields",
}
preference_div_ids = {v: k for k, v in preference_div_names.items()}


def read_preferences_page(soup: BeautifulSoup) -> PreferenceForm:
    """
    :param soup:
    :return:
    """
    form = soup.find("form", {"name": "formMain"})
    preference_form = PreferenceForm(form)
    company_information = CompanyInformation.from_soup(form)
    payroll_preferences = PayrollPreferences.from_soup(form)
    overtime_preferences = OvertimePreferences.from_soup(form)
    device_preferences = DevicePreferences.from_soup(form)
    punch_preferences = PunchPreferences.from_soup(form)
    alert_preferences = AlertPreferences.from_soup(form)
    multi_clock_preferences = MultiClockPreferences.from_soup(form)
    custom_field_preferences = CustomFieldPreferences.from_soup(form)
    email_preferences = EmailPreferences.from_soup(form)
    device_information = DeviceInformation.from_soup(form)
    employee_input_preferences = EmployeeInputPreferences.from_soup(form)

    return Preferences(preference_form=preference_form, company_information=company_information,
                       payroll_preferences=payroll_preferences, overtime_preferences=overtime_preferences,
                       device_preferences=device_preferences, punch_preferences=punch_preferences,
                       alert_preferences=alert_preferences, multi_clock_preferences=multi_clock_preferences,
                       custom_field_preferences=custom_field_preferences, email_preferences=email_preferences,
                       device_information=device_information, employee_input_preferences=employee_input_preferences)
