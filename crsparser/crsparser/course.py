import re

class Course(object):
    """
    A course in the course catalog, consisting of multiple lectures. Contains
    information about: department; course name; lectures; number of units.
    """
    INFO_KEYS = ["same_as",         # string, "SAME AS: [etc.]"
                 "restrict",        # string, "RESTRICT: [etc.]"
                 "xc",              # examination code as an int
                 "grade_type",      # two-letter grade type, e.g. "SO"
                 "units"]           # integer number of units
    
    def __init__(self, dept, name, number, lec_list, info_dict):
        """
        Arguments:

        dept - name of department
        name - name of course, e.g. "SOFTWARE CONST LAB"
        number - string of catalog number + suffix if any, e.g. "35L"
        lec_list - list of lectures
        info_dict - dict of info, with keys from Course.INFO_KEYS
        """
        self.dept = dept
        self.name = name
        self.number = number
        self.lectures = lectures
        self.info_dict = info_dict
    
    def duration(self):
        """
        Returns the duration of this a course lecture. Assumes that all lectures
        have the same duration, and that at least one lecture exists.
        """
        return self.lectures[0].time_intv.duration()
        
    def islab(self):
        """Returns true if this course is a lab (has an "L" in its name)."""
        return "l" in self.name.lower()
        
    def isupperdiv(self):
        """Returns true if this course is an upper division course."""
        return util.stoi(self.number) >= 100
        
    def starts_at(self, time):
        """
        Returns true if this course contains a lecture that begins at the
        specified time (Time object).
        """
        for lec in lectures:
            if lec.time_intv.start == time:
                return True
        return False
        
    def ends_at(self, time):
        """
        Returns true if this course contains a lecture that ends at the
        specified time (Time object).
        """
        for lec in lectures:
            if lec.time_intv.end == time:
                return True
        return False

class Lecture(object):
    """
    One lecture (of possibly many) in a course. Contains information about: days 
    the lecture is held; professor name; lecture hours; list of Discussions.
    """
    def __init__(self, number, days, prof_name, time_intv, capacity, disc_list):
        """
        Arguments:

        name - number of lecture (e.g. 2)
        days - subset of "MTWRF"
        prof_name - name of TA
        time_intv - TimeInterval representing lecture hours
        capacity - number of spots available
        disc_list - list of Discussions
        """
        self.name = name
        self.days = days
        self.prof_name = prof_name
        self.time_intv = time_intv
        self.capacity = capacity
        self.disc_list = disc_list

class Discussion(object):
    """
    One of multiple discussions for a lecture. Contains information about:
    day held; TA name; discussion hours.
    """
    DISC_FSTR = "{0} [{1}] {2} | {3}"
    
    def __init__(self, name, day, ta_name, time_intv):
        """
        Arguments:

        name - name of lecture (e.g. "1D")
        day - single character from "MTWRF"
        ta_name - name of TA
        time_intv - TimeInterval representing discussion hours
        """
        self.name = name
        self.day = day
        self.ta_name = ta_name
        self.time_intv = time_intv

    def __str__(self):
        return DISC_FSTR.format(self.name, self.day,
                                str(self.time_intv), self.ta_name)
