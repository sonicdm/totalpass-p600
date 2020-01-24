from totalpass_p600.punches import Punches


class Employee:
    """An employee and their dog"""

    def __init__(self, first, mi, last, visid, eid):
        self.eid = eid
        self.badge = visid
        self.wage = None
        self.fname = first
        self.lname = last
        self.department = None
        if mi:
            self.mi = mi
        else:
            self.mi = ""
        self.visid = visid
        self.punches = Punches()

    def add_punch(self, punch_record):
        self.punches.add_punch(punch_record)

    def add_punches(self, punches):
        self.punches.add_punches(punches)

    def __repr__(self):
        return "<Employee #{visid}: {lname}, {fname}>".format(
            visid=self.visid,
            fname=self.fname,
            lname=self.lname,
        )


class Employees:

    def __init__(self):
        self._employees = {}

    def add_employee(self,first, mi, last, visid, eid):
        self._employees[visid] = Employee(first, mi, last, visid, eid)
    pass