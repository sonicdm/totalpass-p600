from datetime import time, date
from pathlib import Path
from unittest import TestCase

from bs4 import BeautifulSoup

from totalpass_p600.timeclock_preferences import (Preferences, PreferenceForm, PayrollPreferences, OvertimePreferences,
                                                  EmployeeInputPreferences, MultiClockPreferences, CustomField,
                                                  CustomFieldPreferences, DevicePreferences,
                                                  PunchPreferences, AlertPreferences, EmailPreferences,
                                                  CompanyInformation, DeviceInformation, HiddenInputs, str_to_time)

html_file = r"./test_data/preferences.html"

pref_file = Path(html_file)
pref_html = pref_file.read_text()
pref_soup = BeautifulSoup(pref_html, 'html.parser')
form_soup = pref_soup.find('form', {'id': 'formMain'})


class TestValidateTime(TestCase):

    def test_validate_time(self):
        """
        times must be in format HH:MMa or HH:MMp
        returns time object
        :return:
        """
        valid_time_12_am = "12:00a"
        valid_time_12_pm = "12:00p"
        invalid_time_12_am = "12:00"
        invalid_time_12_pm = "12:00"
        invalid_time_24_am = "24:00a"
        invalid_time_24_pm = "24:00p"
        invalid_time_format = "12:00 a"

        self.assertEqual(str_to_time(valid_time_12_am), time(0, 0))
        self.assertEqual(str_to_time(valid_time_12_pm), time(12, 0))
        with self.assertRaises(ValueError):
            str_to_time(invalid_time_12_am)
        with self.assertRaises(ValueError):
            str_to_time(invalid_time_12_pm)
        with self.assertRaises(ValueError):
            str_to_time(invalid_time_24_am)
        with self.assertRaises(ValueError):
            str_to_time(invalid_time_24_pm)
        with self.assertRaises(ValueError):
            str_to_time(invalid_time_format)


class TestPayrollPreferences(TestCase):
    def test_validate_week_start(self):
        valid_week_start = "Mon"
        upper_week_start = "MON"
        lower_week_start = "mon"
        invalid_week_start = "Foo"
        self.assertEqual(PayrollPreferences.validate_week_start(valid_week_start), valid_week_start.title())
        self.assertEqual(PayrollPreferences.validate_week_start(upper_week_start), upper_week_start.title())
        self.assertEqual(PayrollPreferences.validate_week_start(lower_week_start), lower_week_start.title())
        with self.assertRaises(ValueError):
            PayrollPreferences.validate_week_start(invalid_week_start)

    def test_validate_pay_dates(self):
        valid_pay_date = "11/22/21"
        invalid_pay_date_invalid_format = "11/22/21/22"
        invalid_pay_date_invalid_month = "13/22/21"
        invalid_pay_date_invalid_day = "11/32/21"
        invalid_pay_date_invalid_year = "11/22/21/22"
        self.assertEqual(PayrollPreferences.validate_pay_dates(valid_pay_date), date(2021, 11, 22))
        with self.assertRaises(ValueError):
            PayrollPreferences.validate_pay_dates(invalid_pay_date_invalid_format)
        with self.assertRaises(ValueError):
            PayrollPreferences.validate_pay_dates(invalid_pay_date_invalid_month)
        with self.assertRaises(ValueError):
            PayrollPreferences.validate_pay_dates(invalid_pay_date_invalid_day)
        with self.assertRaises(ValueError):
            PayrollPreferences.validate_pay_dates(invalid_pay_date_invalid_year)

    def test_validate_pay_period_type(self):
        """'weekly', 'bi-weekly', 'monthly', 'semi-monthly'"""
        valid_pay_period_type = "weekly"
        upper_pay_period_type = "WEEKLY"
        lower_pay_period_type = "weekly"
        title_pay_period_type = "Weekly"
        bi_weekly_pay_period_type = "bi-weekly"
        monthly_pay_period_type = "monthly"
        semi_monthly_pay_period_type = "semi-monthly"
        invalid_pay_period_type = "Foo"
        self.assertEqual(PayrollPreferences.validate_pay_period_type(valid_pay_period_type),
                         valid_pay_period_type.title())
        self.assertEqual(PayrollPreferences.validate_pay_period_type(upper_pay_period_type),
                         upper_pay_period_type.title())
        self.assertEqual(PayrollPreferences.validate_pay_period_type(lower_pay_period_type),
                         lower_pay_period_type.title())
        self.assertEqual(PayrollPreferences.validate_pay_period_type(title_pay_period_type),
                         title_pay_period_type.title())
        self.assertEqual(PayrollPreferences.validate_pay_period_type(bi_weekly_pay_period_type),
                         bi_weekly_pay_period_type.title())
        self.assertEqual(PayrollPreferences.validate_pay_period_type(monthly_pay_period_type),
                         monthly_pay_period_type.title())
        self.assertEqual(PayrollPreferences.validate_pay_period_type(semi_monthly_pay_period_type),
                         semi_monthly_pay_period_type.title())

        with self.assertRaises(ValueError):
            PayrollPreferences.validate_pay_period_type(invalid_pay_period_type)

    def test_from_soup(self):
        prefs = PayrollPreferences.from_soup(form_soup)
        self.assertEqual(prefs.pay_period_type, "Bi-Weekly")
        self.assertEqual(prefs.last_pay_start, date(2021, 12, 5))
        self.assertEqual(prefs.this_pay_start, date(2021, 12, 19))
        self.assertEqual(prefs.next_pay_start, date(2022, 1, 2))
        self.assertEqual(prefs.day_start, time(0, 0))
        self.assertEqual(prefs.week_start, "Sun")


class TestOvertimePreferences(TestCase):
    def test_validate_consecutive_day_ot(self):
        valid_yes = "Yes"
        valid_no = "No"
        invalid_consecutive_day_ot = "Foo"
        self.assertEqual(OvertimePreferences.validate_consecutive_day_ot(valid_yes), "Yes")
        self.assertEqual(OvertimePreferences.validate_consecutive_day_ot(valid_no), "No")
        self.assertEqual(OvertimePreferences.validate_consecutive_day_ot(False), "No")
        self.assertEqual(OvertimePreferences.validate_consecutive_day_ot(True), "Yes")
        with self.assertRaises(ValueError):
            OvertimePreferences.validate_consecutive_day_ot(invalid_consecutive_day_ot)

    def test_from_soup(self):
        prefs = OvertimePreferences.from_soup(form_soup)
        self.assertEqual(prefs.consecutive_day_ot, "No")
        self.assertEqual(prefs.day_ot1_after_hours, 99.00)
        self.assertEqual(prefs.day_ot2_after_hours, 99.00)
        self.assertEqual(prefs.week_ot1_after_hours, 40.00)
        self.assertEqual(prefs.week_ot2_after_hours, 99.00)
        self.assertEqual(prefs.ot1_multiplier, 1.5)
        self.assertEqual(prefs.ot2_multiplier, 2.0)


class TestPunchPreferences(TestCase):
    def test_validate_ip_addresses(self):
        valid_ip_address = "169.222.35.1"
        valid_ip_addresses = "169.222.35.1, 192.168.1.5"
        invalid_ip_addresses_one_bad = "1234.5678.9012.3456, 192.168.1.1"
        invalid_ip_addresses_two_bad = "1234.5678.9012.3456, 256.256.256.256"
        invalid_ip_addresses_three_bad = "1234.5678.9012.3456, 256.256.256.256, 401.256.256.256"
        invalid_ip_address = "259.222.35.1"
        self.assertEqual(PunchPreferences.validate_ip_addresses(valid_ip_address), valid_ip_address.split(","))
        self.assertEqual(PunchPreferences.validate_ip_addresses(valid_ip_addresses), valid_ip_addresses.split(","))
        with self.assertRaises(ValueError):
            PunchPreferences.validate_ip_addresses(invalid_ip_addresses_one_bad)
        with self.assertRaises(ValueError):
            PunchPreferences.validate_ip_addresses(invalid_ip_addresses_two_bad)
        with self.assertRaises(ValueError):
            PunchPreferences.validate_ip_addresses(invalid_ip_addresses_three_bad)
        with self.assertRaises(ValueError):
            PunchPreferences.validate_ip_addresses(invalid_ip_address)

    def test_validate_rounding_type(self):
        valid_rounding_types = ['None', '15 Minute', '15 Minute Slant', '10th Hour']
        lower_case_valid_rounding_types = ['none', '15 minute', '15 minute slant', '10th hour']
        upper_case_valid_rounding_types = ['NONE', '15 MINUTE', '15 MINUTE SLANT', '10TH HOUR']
        invalid_rounding_types = ['Foo', 'Bar', 'Baz']
        for valid_rounding_type in valid_rounding_types:
            self.assertEqual(PunchPreferences.validate_rounding_type(valid_rounding_type), valid_rounding_type.lower())

        for lower_case_valid_rounding_type in lower_case_valid_rounding_types:
            self.assertEqual(PunchPreferences.validate_rounding_type(lower_case_valid_rounding_type),
                             lower_case_valid_rounding_type)

        for upper_case_valid_rounding_type in upper_case_valid_rounding_types:
            self.assertEqual(PunchPreferences.validate_rounding_type(upper_case_valid_rounding_type),
                             upper_case_valid_rounding_type.lower())

        with self.assertRaises(ValueError):
            PunchPreferences.validate_rounding_type(invalid_rounding_types[0])

    def test_from_soup(self):
        prefs = PunchPreferences.from_soup(form_soup)
        self.assertEqual(prefs.rounding_type, "none")
        self.assertEqual(prefs.auto_punch_in_after_hours, 15.00)
        self.assertEqual(prefs.flag_edits_on_reports, True)
        self.assertEqual(prefs.reject_like_punches_range, 2)
        self.assertEqual(prefs.global_authorized_web_punch_addresses, ["192.168.1.167"])


class TestHiddenInputs(TestCase):

    def test_hidden_inputs(self):
        hidden_inputs = HiddenInputs(form_soup)
        pass


class TestEmployeeInputPreferences(TestCase):
    """
    fields:
    enabled: bool
    Input Name
    Collection Type: Currency, Number
    Collect On: OUT, IN
    Show Totals: bool
    """

    def test_validate_collection_type(self):
        valid_collection_types = ['Currency', 'Number']
        invalid_collection_types = ['Foo', 'Bar']
        for valid_collection_type in valid_collection_types:
            self.assertEqual(EmployeeInputPreferences.validate_collection_type(valid_collection_type),
                             valid_collection_type.title())

        with self.assertRaises(ValueError):
            EmployeeInputPreferences.validate_collection_type(invalid_collection_types[0])

    def test_validate_collect_on(self):
        valid_collect_ons = ['IN', 'OUT']
        invalid_collect_ons = ['Foo', 'Bar']
        for valid_collect_on in valid_collect_ons:
            self.assertEqual(EmployeeInputPreferences.validate_collect_on(valid_collect_on), valid_collect_on.upper())

        with self.assertRaises(ValueError):
            EmployeeInputPreferences.validate_collect_on(invalid_collect_ons[0])

    def test_from_soup(self):
        prefs = EmployeeInputPreferences.from_soup(form_soup)
        self.assertEqual(prefs.enabled, False)
        self.assertEqual(prefs.input_name, "Tips")
        self.assertEqual(prefs.collection_type, "Currency")
        self.assertEqual(prefs.collect_on, "OUT")
        self.assertEqual(prefs.show_totals, True)


class TestDeviceInformation(TestCase):
    """
    fields:
    Database Version:1510191
    Software Version:8790
    Serial Number:T002-060-549
    """

    def test_from_soup(self):
        device_info = DeviceInformation.from_soup(form_soup)
        self.assertEqual(device_info.database_version, "1510191")
        self.assertEqual(device_info.software_version, "8790")
        self.assertEqual(device_info.serial_number, "T002-060-549")


class TestDevicePreferences(TestCase):
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

    def test_validate_calculated_time_format(self):
        valid_calculated_time_formats = ['hundredths', 'minutes']
        invalid_calculated_time_formats = ['Foo', 'Bar']
        for valid_calculated_time_format in valid_calculated_time_formats:
            self.assertEqual(DevicePreferences.validate_calculated_time_format(valid_calculated_time_format),
                             valid_calculated_time_format.title())

        with self.assertRaises(ValueError):
            DevicePreferences.validate_calculated_time_format(invalid_calculated_time_formats[0])

    def test_validate_default_report_to(self):
        valid_default_report_tos = ['Today', 'Yesterday', 'Last Week', 'This Week', 'Last Pay', 'This Pay']
        lower_valid_default_report_tos = [x.lower() for x in valid_default_report_tos]
        upper_valid_default_report_tos = [x.upper() for x in valid_default_report_tos]
        invalid_default_report_tos = ['Foo', 'Bar']
        for valid_default_report_to in valid_default_report_tos:
            self.assertEqual(DevicePreferences.validate_default_report_to(valid_default_report_to),
                             valid_default_report_to)

        for lower_valid_default_report_to in lower_valid_default_report_tos:
            self.assertEqual(DevicePreferences.validate_default_report_to(lower_valid_default_report_to),
                             lower_valid_default_report_to.title())

        for upper_valid_default_report_to in upper_valid_default_report_tos:
            self.assertEqual(DevicePreferences.validate_default_report_to(upper_valid_default_report_to),
                             upper_valid_default_report_to.title())

        with self.assertRaises(ValueError):
            DevicePreferences.validate_default_report_to(invalid_default_report_tos[0])

    def test_validate_use_popup_windows_for_edits(self):
        valid_use_popup_windows_for_edits_lower = ['yes', 'no', 'yes with batch edits']
        valid_use_popup_windows_for_edits_upper = ['YES', 'NO', 'YES WITH BATCH EDITS']
        valid_use_popup_windows_for_edits_title = ['Yes', 'No', 'Yes With Batch Edits']
        invalid_use_popup_windows_for_edits = ['Foo', 'Bar']
        for valid_use_popup_windows_for_edit in valid_use_popup_windows_for_edits_lower:
            self.assertEqual(DevicePreferences.validate_use_popup_windows_for_edits(valid_use_popup_windows_for_edit),
                             valid_use_popup_windows_for_edit.title())

        for valid_use_popup_windows_for_edit in valid_use_popup_windows_for_edits_upper:
            self.assertEqual(DevicePreferences.validate_use_popup_windows_for_edits(valid_use_popup_windows_for_edit),
                             valid_use_popup_windows_for_edit.title())

        for valid_use_popup_windows_for_edit in valid_use_popup_windows_for_edits_title:
            self.assertEqual(DevicePreferences.validate_use_popup_windows_for_edits(valid_use_popup_windows_for_edit),
                             valid_use_popup_windows_for_edit)

        with self.assertRaises(ValueError):
            DevicePreferences.validate_use_popup_windows_for_edits(invalid_use_popup_windows_for_edits[0])

    def test_from_soup(self):
        prefs = DevicePreferences.from_soup(form_soup)
        self.assertEqual(prefs.calculated_time_format, 'Hundredths')
        self.assertEqual(prefs.pin_number_length, 5)
        self.assertFalse(prefs.hide_employee_pin)
        self.assertEqual(prefs.system_prompt_1, 'Enter Emp #')
        self.assertEqual(prefs.system_prompt_2, 'Enter Emp #')
        self.assertEqual(prefs.system_prompt_3, 'Enter Emp #')
        self.assertEqual(prefs.supervisor_code, '00 00 00')
        self.assertFalse(prefs.lock_keypad)
        self.assertTrue(prefs.use_daylight_savings)
        self.assertEqual(prefs.default_attendance_report_to, 'Today')
        self.assertEqual(prefs.default_timecard_report_to, 'Last Pay')
        self.assertEqual(prefs.refresh_home_page_every_x_minutes, 15)
        self.assertFalse(prefs.use_ssl_server)
        self.assertEqual(prefs.use_popup_windows_for_edits, "Yes")
        self.assertTrue(prefs.show_total_hours_at_the_clock)


class TestMultiClockPreferences(TestCase):
    """
    Child realtime Time/Date sync: bool
    Child realtime data sync: bool
    Child Online sync delay x seconds: int
    Child Offline sync delay x seconds: int
    """

    def test_from_soup(self):
        prefs = MultiClockPreferences.from_soup(form_soup)
        self.assertTrue(prefs.child_realtime_time_date_sync)
        self.assertTrue(prefs.child_realtime_data_sync)
        self.assertEqual(prefs.child_online_sync_delay_seconds, 300)
        self.assertEqual(prefs.child_offline_sync_delay_seconds, 60)


class TestEmailPreferences(TestCase):
    """
    fields:
    SMTP Server Address: 192.168.1.167
    Use SSL: bool: False
    Use STARTTLS: bool: False
    Use Authentication: bool: False
    Username/Email Address: str
    Password: str: ""
    From Email Address: str: office@capellamarket.com
    Email Domain Name: str : capellamarket.com
    Email Backups To: str: office@capellamarket.com
    Send Backups: Daily, Weekly, Monthly: Daily
    """

    def test_send_backups_validator(self):
        valid_send_backups = ['Daily', 'Weekly', 'Monthly']
        for valid_send_backup in valid_send_backups:
            self.assertEqual(EmailPreferences.send_backups_validator(valid_send_backup), valid_send_backup)

        with self.assertRaises(ValueError):
            EmailPreferences.send_backups_validator('Foo')

    def test_from_soup(self):
        prefs = EmailPreferences.from_soup(form_soup)
        self.assertEqual(prefs.smtp_server_address, '192.168.1.167')
        self.assertFalse(prefs.use_ssl)
        self.assertFalse(prefs.use_starttls)
        self.assertFalse(prefs.use_authentication)
        self.assertEqual(prefs.username_email_address, '')
        self.assertEqual(prefs.password, '')
        self.assertEqual(prefs.from_email_address, 'office@capellamarket.com')
        self.assertEqual(prefs.email_domain_name, 'capellamarket.com')
        self.assertEqual(prefs.email_backups_to, 'office@capellamarket.com')
        self.assertEqual(prefs.send_backups, 'Daily')


class TestAlertPreferences(TestCase):
    """
    Alert Low Hours at x.xx Hours per punch: 0.0
    Alert High Hours at x.xx Hours per punch: 14.0
    Maximum Punch Time at x.xx Hours per punch: 24.0
    Alert Day Overtime OT at x.xx Hours remaining: 2
    Alert Week Overtime OT at x.xx Hours remaining: 0
    Check Alerts Every x Minutes: 15
    Email Alerts Every x Minutes: 15
    Update Employee Hours Every x Minutes: 15
    Email Daily Alerts at mm:hh(a/p): 12:00a
    """

    def test_from_soup(self):
        prefs = AlertPreferences.from_soup(form_soup)
        self.assertEqual(prefs.alert_low_hours_threshold, 0.0)
        self.assertEqual(prefs.alert_high_hours_threshold, 14.0)
        self.assertEqual(prefs.maximum_punch_time_threshold, 24.0)
        self.assertEqual(prefs.day_overtime_threshold, 2)
        self.assertEqual(prefs.week_overtime_threshold, 0)
        self.assertEqual(prefs.check_alerts_interval, 15)
        self.assertEqual(prefs.email_alerts_interval, 15)
        self.assertEqual(prefs.update_employee_hours_interval, 15)
        self.assertEqual(prefs.email_daily_alerts_time, time(0, 0))


class TestCustomFieldPreferences(TestCase):
    def test_from_soup(self):
        custom_field_1 = CustomField(name="Field 1", assign="None")
        custom_field_2 = CustomField(name="Field 2", assign="None")
        custom_field_3 = CustomField(name="Field 3", assign="None")
        custom_field_4 = CustomField(name="Field 4", assign="None")
        custom_field_5 = CustomField(name="Field 5", assign="None")
        custom_field_6 = CustomField(name="Field 6", assign="None")
        custom_field_7 = CustomField(name="Field 7", assign="None")
        custom_field_8 = CustomField(name="Field 8", assign="None")
        custom_field_9 = CustomField(name="Field 9", assign="None")
        custom_field_10 = CustomField(name="Field 10", assign="None")

        prefs = CustomFieldPreferences.from_soup(form_soup)
        self.assertEqual(prefs.field_1, custom_field_1)
        self.assertEqual(prefs.field_2, custom_field_2)
        self.assertEqual(prefs.field_3, custom_field_3)
        self.assertEqual(prefs.field_4, custom_field_4)
        self.assertEqual(prefs.field_5, custom_field_5)
        self.assertEqual(prefs.field_6, custom_field_6)
        self.assertEqual(prefs.field_7, custom_field_7)
        self.assertEqual(prefs.field_8, custom_field_8)
        self.assertEqual(prefs.field_9, custom_field_9)
        self.assertEqual(prefs.field_10, custom_field_10)


class TestPreferenceForm(TestCase):

    def test_preference_form(self):
        form = PreferenceForm(form_soup)
        self.assertEqual(form.name, 'formMain')
        self.assertEqual(form.action, '')
        self.assertEqual(form.method, 'post')
        self.assertEqual(form.id, 'formMain')
        self.assertIsInstance(form.hidden_inputs, HiddenInputs)


class TestPreferences(TestCase):
    def test_from_soup(self):
        preferences = Preferences.from_soup(pref_soup)
        self.assertIsInstance(preferences, Preferences)
        self.assertIsInstance(preferences.company_information, CompanyInformation)
        self.assertIsInstance(preferences.payroll_preferences, PayrollPreferences)
        self.assertIsInstance(preferences.overtime_preferences, OvertimePreferences)
        self.assertIsInstance(preferences.punch_preferences, PunchPreferences)
        self.assertIsInstance(preferences.employee_input_preferences, EmployeeInputPreferences)
        self.assertIsInstance(preferences.device_information, DeviceInformation)
        self.assertIsInstance(preferences.device_preferences, DevicePreferences)
        self.assertIsInstance(preferences.multi_clock_preferences, MultiClockPreferences)
        self.assertIsInstance(preferences.email_preferences, EmailPreferences)
        self.assertIsInstance(preferences.alert_preferences, AlertPreferences)
        self.assertIsInstance(preferences.custom_field_preferences, CustomFieldPreferences)
        self.assertIsInstance(preferences.preferences_form, PreferenceForm)

    def test_from_html(self):
        preferences = Preferences.from_html(pref_html)
        self.assertIsInstance(preferences, Preferences)
        self.assertIsInstance(preferences, Preferences)
        self.assertIsInstance(preferences.company_information, CompanyInformation)
        self.assertIsInstance(preferences.payroll_preferences, PayrollPreferences)
        self.assertIsInstance(preferences.overtime_preferences, OvertimePreferences)
        self.assertIsInstance(preferences.punch_preferences, PunchPreferences)
        self.assertIsInstance(preferences.employee_input_preferences, EmployeeInputPreferences)
        self.assertIsInstance(preferences.device_information, DeviceInformation)
        self.assertIsInstance(preferences.device_preferences, DevicePreferences)
        self.assertIsInstance(preferences.multi_clock_preferences, MultiClockPreferences)
        self.assertIsInstance(preferences.email_preferences, EmailPreferences)
        self.assertIsInstance(preferences.alert_preferences, AlertPreferences)
        self.assertIsInstance(preferences.custom_field_preferences, CustomFieldPreferences)
        self.assertIsInstance(preferences.preferences_form, PreferenceForm)


class TestCompanyInformation(TestCase):
    def test_from_soup(self):
        company_info = CompanyInformation.from_soup(form_soup)
        self.assertIsInstance(company_info, CompanyInformation)
        self.assertEqual(company_info.company_name, 'Capella Market')
        self.assertEqual(company_info.company_payroll_id, '2489')
