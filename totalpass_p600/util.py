import calendar
from datetime import timedelta, datetime, date
from typing import Union


def strings_to_numbers(l, fmt='float'):
    """
    Turn number string into the specified format from a list of values or a single string

    >>> strings_to_numbers(['1', 'a', '2.34', 3])
    [1, 'a', 2.34, 3]
    >>> strings_to_numbers('2.34')
    2.34
    >>> strings_to_numbers('Hi There')
    'Hi There'
    >>> strings_to_numbers('   123456')
    123456
    >>> strings_to_numbers(False)
    """

    def _convert(s):
        if not s:
            return s
        try:
            if float(s).is_integer():
                return int(float(s))
            else:
                return float(s)
        except (ValueError, TypeError):
            return s

    if not l:
        return l
    if hasattr(l, "__iter__") and not isinstance(l, (str, int)):
        o = []
        for i in l:
            o.append(_convert(i))
        return o
    else:
        return _convert(l)


def date_to_datetime(date_obj, datetime_obj=None, hour=0, minute=0, second=0):
    """
    Combine a date and a datetime to get that datetime for that date
    :type date_obj: date
    :type datetime_obj: datetime
    :type hour: int
    :type second: int
    :type minute: int
    """
    if datetime_obj:
        # hour = datetime_obj.hour
        # minute = datetime_obj.minute
        # second = datetime_obj.second
        return datetime_obj.combine(date_obj, datetime_obj.time())

    return datetime(date_obj.year, date_obj.month, date_obj.day, hour, minute, second)


def get_time_range(start: Union[date, datetime],
                   stop: Union[date, datetime] = None,
                   span_unit: str = 'days') -> list[datetime]:
    """
    return a list of times based on the span type chosen with start and stop datetime objects
    :param: span_unit: days, weeks, months, years, hours, minutes, seconds. Default is days
    :rtype list of datetime
    """
    valid_span_units = ['seconds', 'minutes', 'hours', 'days', 'weeks', 'months', 'years']
    if span_unit not in valid_span_units:
        raise ValueError('Invalid span unit: {}'.format(span_unit))
    # if start or stop is are dates, convert to datetime
    if isinstance(start, date):
        start = date_to_datetime(start)
    if isinstance(stop, date):
        stop = date_to_datetime(stop)

    # if start is after stop, swap them

    # if span_unit is days, convert to timedelta
    if span_unit == 'days':
        span = timedelta(days=1)
    elif span_unit == 'weeks':
        span = timedelta(weeks=1)
    elif span_unit == 'months':
        span = timedelta(days=30)
    elif span_unit == 'years':
        span = timedelta(days=365)
    elif span_unit == 'hours':
        span = timedelta(seconds=60 * 60)
    else:
        span = timedelta(seconds=60)

    if not stop and span_unit == 'days':
        return [start]
    elif not stop:
        stop = start + span

    if start > stop:
        start, stop = stop, start
    # get the list of times
    times = []
    current = start
    while current <= stop:
        times.append(current)
        current += span
    return times


def get_date_time_frame_span(time_span: str, start_date: Union[date, datetime] = None,
                             week_start_day: str = "sunday") -> tuple[datetime, datetime]:
    """
    Get the time frame for a given name using calendar for accurate month days
    :param time_span: Today, Yesterday, Tomorrow, Last Week, This Week, Next Week, Last Month,
                This Month, Next Month, Last Year, This Year, Next Year, Year to date,
                Month to date, Week to date, Year, Week, Month
    :param start_date: The start day for the time frame. If not provided, the current day is used
    :param week_start_day: Can be sunday or monday. Default is sunday
    :return:
    """
    time_span_presets = ['today', 'yesterday', 'tomorrow', 'last_week', 'this_week', 'next_week',
                         'last_month', 'this_month', 'next_month', 'last_year', 'this_year',
                         'next_year', 'year_to_date', 'month_to_date', 'week_to_date', 'year',
                         'week', 'month']
    time_span = to_snake_case(time_span)
    if time_span not in time_span_presets:
        raise ValueError('Invalid time span: {}'.format(time_span))

    if not start_date:
        start_date = date.today()

    this_month_length = calendar.monthrange(start_date.year, start_date.month)[1]
    today_month = start_date.month
    today_day = start_date.day
    today_year = start_date.year

    if week_start_day == 'sunday':
        start_date_weekday = start_date.isoweekday()
        # if today is not sunday, then the first day of the week is the previous sunday
        if start_date_weekday != 7:
            week_start = start_date - timedelta(days=start_date_weekday)
        else:
            week_start = start_date
    elif week_start_day == 'monday':
        # if today is not monday then the first day of the week is the previous monday
        start_date_weekday = start_date.weekday()
        if start_date_weekday != 0:
            week_start = start_date - timedelta(days=start_date_weekday)
        else:
            week_start = start_date
    else:
        raise ValueError('Invalid week start day: {}'.format(week_start_day))

    week_end = week_start + timedelta(days=6)
    start_of_week = week_start
    end_of_week = week_end

    # last week
    start_of_last_week = start_of_week - timedelta(days=7)
    end_of_last_week = end_of_week - timedelta(days=7)
    # next week
    start_of_next_week = start_of_week + timedelta(days=7)
    end_of_next_week = end_of_week + timedelta(days=7)
    # this month
    start_of_month = date(today_year, today_month, 1)
    end_of_month = date(today_year, today_month, this_month_length)
    # last month might be in the previous year
    if today_month == 1:
        last_month_length = calendar.monthrange(today_year - 1, 12)[1]
        last_month = 12
        last_year = today_year - 1
    else:
        last_month_length = calendar.monthrange(today_year, today_month - 1)[1]
        last_month = today_month - 1
        last_year = today_year
    start_of_last_month = date(last_year, last_month, 1)
    end_of_last_month = date(last_year, last_month, last_month_length)
    # next month might be in the next year
    if today_month == 12:
        next_month_length = calendar.monthrange(today_year + 1, 1)[1]
        next_month = 1
        next_year = today_year + 1
    else:
        next_month_length = calendar.monthrange(today_year, today_month + 1)[1]
        next_month = today_month + 1
        next_year = today_year
    start_of_next_month = date(next_year, next_month, 1)
    end_of_next_month = date(next_year, next_month, next_month_length)

    # this year
    start_of_year = date(today_year, 1, 1)
    end_of_year = date(today_year, 12, 31)
    # last year
    start_of_last_year = date(today_year - 1, 1, 1)
    end_of_last_year = date(today_year - 1, 12, 31)
    # next year
    start_of_next_year = date(today_year + 1, 1, 1)
    end_of_next_year = date(today_year + 1, 12, 31)

    # year to date
    start_of_year_to_date = date(today_year, 1, 1)
    end_of_year_to_date = start_date
    # month to date
    start_of_month_to_date = date(today_year, today_month, 1)
    end_of_month_to_date = start_date
    # week to date
    start_of_week_to_date = start_of_week
    end_of_week_to_date = start_date

    year_span_start = start_date.replace(year=start_date.year - 1)
    year_span_end = start_date
    # month span start may be in the previous year
    if today_month == 1:
        month_span_start = date(today_year - 1, 12, start_date.day)
    else:
        month_span_start = date(today_year, today_month - 1, start_date.day)
    month_span_end = start_date
    # week span start may be in the previous year
    week_span_start = start_date - timedelta(days=7)
    week_span_end = start_date

    time_spans = {
        'today': (start_date, start_date),
        'yesterday': (start_date - timedelta(days=1), start_date - timedelta(days=1)),
        'this_week': (start_of_week, end_of_week),
        'last_week': (start_of_last_week, end_of_last_week),
        'next_week': (start_of_next_week, end_of_next_week),
        'this_month': (start_of_month, end_of_month),
        'last_month': (start_of_last_month, end_of_last_month),
        'next_month': (start_of_next_month, end_of_next_month),
        'this_year': (start_of_year, end_of_year),
        'last_year': (start_of_last_year, end_of_last_year),
        'next_year': (start_of_next_year, end_of_next_year),
        'year_to_date': (start_of_year_to_date, end_of_year_to_date),
        'month_to_date': (start_of_month_to_date, end_of_month_to_date),
        'week_to_date': (start_of_week_to_date, end_of_week_to_date),
        'year': (year_span_start, year_span_end),
        'month': (month_span_start, month_span_end),
        'week': (week_span_start, week_span_end),
    }
    return time_spans[time_span]


def to_snake_case(s):
    """
    Convert a string to snake case
    :type s: str
    :rtype: str
    """
    return s.replace(' ', '_').lower()


def normalize_dict(d, prefix='', sep='_'):
    """
    Flatten a nested dictionary into a single level dictionary
    {'a': {'b': {'c': 1}}} -> {'a.b.c': 1}
    :type d: dict
    :type prefix: str
    :type sep: str
    :rtype: dict
    """
    if not isinstance(d, dict):
        return d
    o = {}
    for k, v in d.items():
        if isinstance(v, dict):
            o.update(normalize_dict(v, prefix=prefix + k + sep, sep=sep))
        else:
            o[prefix + k] = v
    return o
