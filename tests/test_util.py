from unittest import TestCase


class TestNormalizeDict(TestCase):
    def test_normalize_dict(self):
        from totalpass_p600.util import normalize_dict
        d = {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': {"e": 4, "f": 5},
            'g': {"h": 6, "i": 7},
            'j': {"k": 8, "l": 9, "m": {"n": 10, "o": 11}},
            'p': {"q": 12, "r": 13, "s": {"t": 14, "u": 15, "v": {"w": 16, "x": 17}}}
        }

        expected = {
            'a': 1,
            'b': 2,
            'c': 3,
            'd.e': 4,
            'd.f': 5,
            'g.h': 6,
            'g.i': 7,
            'j.k': 8,
            'j.l': 9,
            'j.m.n': 10,
            'j.m.o': 11,
            'p.q': 12,
            'p.r': 13,
            'p.s.t': 14,
            'p.s.u': 15,
            'p.s.v.w': 16,
            'p.s.v.x': 17
        }

        self.assertEqual(normalize_dict(d, sep="."), expected)


class TestGetTimeRange(TestCase):
    def test_get_time_range_days(self):
        from totalpass_p600.util import get_time_range
        from datetime import datetime
        start = datetime(2019, 1, 1)
        end = datetime(2019, 1, 5)
        self.assertEqual(get_time_range(start, end),
                         [datetime(2019, 1, 1), datetime(2019, 1, 2), datetime(2019, 1, 3), datetime(2019, 1, 4),
                          datetime(2019, 1, 5)])

    def test_get_time_range_months(self):
        from totalpass_p600.util import get_time_range
        from datetime import datetime
        start = datetime(2019, 1, 1)
        end = datetime(2019, 3, 1)
        self.assertEqual(get_time_range(start, end),
                         [datetime(2019, 1, 1), datetime(2019, 1, 2), datetime(2019, 1, 3), datetime(2019, 1, 4),
                          datetime(2019, 1, 5), datetime(2019, 1, 6), datetime(2019, 1, 7), datetime(2019, 1, 8),
                          datetime(2019, 1, 9), datetime(2019, 1, 10), datetime(2019, 1, 11), datetime(2019, 1, 12),
                          datetime(2019, 1, 13), datetime(2019, 1, 14), datetime(2019, 1, 15), datetime(2019, 1, 16),
                          datetime(2019, 1, 17), datetime(2019, 1, 18), datetime(2019, 1, 19), datetime(2019, 1, 20),
                          datetime(2019, 1, 21), datetime(2019, 1, 22), datetime(2019, 1, 23), datetime(2019, 1, 24),
                          datetime(2019, 1, 25), datetime(2019, 1, 26), datetime(2019, 1, 27), datetime(2019, 1, 28),
                          datetime(2019, 1, 29), datetime(2019, 1, 30), datetime(2019, 1, 31), datetime(2019, 2, 1),
                          datetime(2019, 2, 2), datetime(2019, 2, 3), datetime(2019, 2, 4), datetime(2019, 2, 5),
                          datetime(2019, 2, 6), datetime(2019, 2, 7), datetime(2019, 2, 8), datetime(2019, 2, 9),
                          datetime(2019, 2, 10), datetime(2019, 2, 11), datetime(2019, 2, 12), datetime(2019, 2, 13),
                          datetime(2019, 2, 14), datetime(2019, 2, 15), datetime(2019, 2, 16), datetime(2019, 2, 17),
                          datetime(2019, 2, 18), datetime(2019, 2, 19), datetime(2019, 2, 20), datetime(2019, 2, 21),
                          datetime(2019, 2, 22), datetime(2019, 2, 23), datetime(2019, 2, 24), datetime(2019, 2, 25),
                          datetime(2019, 2, 26), datetime(2019, 2, 27), datetime(2019, 2, 28), datetime(2019, 3, 1)])

    def test_get_time_range_no_stop(self):
        from totalpass_p600.util import get_time_range
        from datetime import datetime
        start = datetime(2019, 1, 1)
        end = None
        self.assertEqual(get_time_range(start, end),
                         [datetime(2019, 1, 1)])

        self.assertEqual(get_time_range(start, None, span_unit="weeks"),
                         [datetime(2019, 1, 1), datetime(2019, 1, 2), datetime(2019, 1, 3), datetime(2019, 1, 4),
                          datetime(2019, 1, 5), datetime(2019, 1, 6), datetime(2019, 1, 7)])


class TestDateToDatetime(TestCase):
    def test_date_to_datetime(self):
        self.fail()


class TestTimeSpan(TestCase):
    def test_get_date_time_frame_span(self):
        from totalpass_p600.util import get_date_time_frame_span
        from datetime import datetime, date
        start = datetime(2022, 1, 1).date()
        this_week = get_date_time_frame_span(time_span="this week", start_date=start)
        self.assertEqual(this_week, (date(2021, 12, 26), date(2022, 1, 1)))

        last_week = get_date_time_frame_span(time_span="last week", start_date=start)
        self.assertEqual(last_week, (date(2021, 12, 19), date(2021, 12, 25)))

        this_month = get_date_time_frame_span(time_span="this month", start_date=start)
        self.assertEqual(this_month, (date(2022, 1, 1), date(2022, 1, 31)))

        last_month = get_date_time_frame_span(time_span="last month", start_date=start)
        self.assertEqual(last_month, (date(2021, 12, 1), date(2021, 12, 31)))

        this_year = get_date_time_frame_span(time_span="this year", start_date=start)
        self.assertEqual(this_year, (date(2022, 1, 1), date(2022, 12, 31)))

        last_year = get_date_time_frame_span(time_span="last year", start_date=start)
        self.assertEqual(last_year, (date(2021, 1, 1), date(2021, 12, 31)))

        next_year = get_date_time_frame_span(time_span="next year", start_date=start)
        self.assertEqual(next_year, (date(2023, 1, 1), date(2023, 12, 31)))

        year_to_date = get_date_time_frame_span(time_span="year to date", start_date=date(2022, 4, 7))
        self.assertEqual(year_to_date, (date(2022, 1, 1), date(2022, 4, 7)))

        yesterday = get_date_time_frame_span(time_span="yesterday", start_date=start)
        self.assertEqual(yesterday, (date(2021, 12, 31), date(2022, 12, 31)))

        month_to_date = get_date_time_frame_span(time_span="month to date", start_date=date(2022, 4, 7))
        self.assertEqual(month_to_date, (date(2022, 4, 1), date(2022, 4, 7)))

        week_to_date = get_date_time_frame_span(time_span="week to date", start_date=date(2022, 1, 1))
        self.assertEqual(week_to_date, (date(2021, 12, 26), date(2022, 1, 1)))

        year_span = get_date_time_frame_span(time_span="year", start_date=date(2022, 4, 1))
        self.assertEqual(year_span, (date(2021, 4, 1), date(2022, 4, 1)))

        week_span = get_date_time_frame_span(time_span="week", start_date=date(2022, 1, 1))
        self.assertEqual(week_span, (date(2021, 12, 25), date(2022, 1, 1)))

        month_span = get_date_time_frame_span(time_span="month", start_date=date(2022, 4, 1))
        self.assertEqual(month_span, (date(2022, 3, 1), date(2022, 4, 1)))
