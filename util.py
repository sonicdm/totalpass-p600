from datetime import timedelta, datetime, date


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
        hour = datetime_obj.hour
        minute = datetime_obj.minute
        second = datetime_obj.second

    return datetime(*date_obj.timetuple()[:6]) + timedelta(hours=hour, minutes=minute, seconds=second)


def get_time_range(start, stop, hours=False, days=False, seconds=False):
    """
    return a range of times based on the segment chosen with start and stop datetime objects
    :type stop: datetime or date
    :type start: datetime or date
    :type seconds: bool
    :type days: bool
    :type hours: bool
    :rtype list of datetime
    """
    if isinstance(start, date):
        start = date_to_datetime(start)
    if isinstance(stop, date):
        stop = date_to_datetime(stop)

    if [hours, days, seconds].count(False) < 2:
        raise ValueError("Only One Option Must Be Selected")
    if hours:
        span = int((stop-start).seconds/60/60)
        return [start + timedelta(hours=x) for x in range(span + 1)]
    elif days:
        span = (stop - start).days
        return [start + timedelta(days=x) for x in range(span + 1)]
    elif seconds:
        span = (stop - start).seconds
        return [start + timedelta(seconds=x) for x in range(span + 1)]
    else:
        span = int((stop-start).seconds/60/60)
        return [start + timedelta(hours=x) for x in range(span + 1)]

