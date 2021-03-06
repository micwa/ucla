import crsparser.util.utils as utils

class Department(object):
    """A department with a name and a list of courses."""
    def __init__(self, name, courses):
        """
        Arguments:

        name = name of department
        courses = list of courses
        """
        self.name = name
        self.courses = courses

    def __str__(self):
        """Returns the department name (self.name)."""
        return self.name

class Course(object):
    """
    A course in the course catalog, consisting of multiple lectures. Contains
    information about: course name and number; lectures.
    """
    def __init__(self, name, number, lec_list):
        """
        Arguments:

        name - name of course, e.g. "SOFTWARE CONST LAB"
        number - string of catalog number + suffix if any, e.g. "35L"
        lec_list - list of lectures
        """
        self.name = name
        self.number = number
        self.lec_list = lec_list

    def __str__(self):
        """Returns the course name appended with a space to its number."""
        return self.number + " " + self.name

    def duration(self):
        """
        Returns the duration of this a course lecture. Assumes that all lectures
        have the same duration, and that at least one lecture exists.
        """
        return self.lec_list[0].time_intv.duration()

    def islab(self):
        """
        Returns true if this course is a lab (has an "L" in its number), and
        false if otherwise.
        """
        return "l" in self.number.lower()

    def isupperdiv(self):
        """
        Returns true if this course is an upper division course, and false
        if otherwise.
        """
        return utils.stoi(self.number) >= 100

    def occurs_after(self, time):
        """
        Returns true if this course starts at or after the given time (Time object),
        and false if otherwise.
        """
        for lec in self.lec_list:
            if lec.time_intv.start >= time:
                return True
        return False

    def occurs_before(self, time):
        """
        Returns true if this course ends at or before the given time (Time object),
        and false if otherwise.
        """
        for lec in self.lec_list:
            if lec.time_intv.end <= time:
                return True
        return False

    def starts_at(self, time):
        """
        Returns true if this course contains a lecture that begins at the
        specified time, and false if otherwise.
        """
        for lec in self.lec_list:
            if lec.time_intv.start == time:
                return True
        return False

    def ends_at(self, time):
        """
        Returns true if this course contains a lecture that ends at the
        specified time, and false if otherwise.
        """
        for lec in self.lec_list:
            if lec.time_intv.end == time:
                return True
        return False

class Lecture(object):
    """
    One lecture (of possibly many) in a course. Contains information about: days
    the lecture is held; professor name; lecture hours; list of Discussions.
    """
    INFO_KEYS = ["loc",             # location
                 "capacity",        # enrollment capacity
                 "xc",              # examination code as an int
                 "grade_type",      # two-letter grade type, e.g. "SO"
                 "units",           # integer number of units
                 "same_as",         # string, "SAME AS: [etc.]"
                 "restrict"]        # string, "RESTRICT: [etc.]"

    # 0 = number, 1 = days (align left), 2 = time_interval, 3 = prof_name
    # 4 = capacity
    LEC_FSTR = "LEC {0} [{1:<3}] {2} | {3} | EnCp: {4}"

    def __init__(self, number, days, prof_name, time_intv, info_dict, disc_list):
        """
        Arguments:

        number - number of lecture (e.g. 2)
        days - subset of "MTWRF"
        prof_name - name of TA
        time_intv - TimeInterval representing lecture hours
        info_dict - dict of info, with keys from Lecture.INFO_KEYS
        disc_list - list of Discussions
        """
        self.number = number
        self.days = days
        self.prof_name = prof_name
        self.time_intv = time_intv
        self.info_dict = info_dict
        self.disc_list = disc_list

    def __str__(self):
        """
        Returns a string representing this lecture (does not include
        discussion information). Every item is aligned until the first pipe.
        """
        return Lecture.LEC_FSTR.format(self.number, self.days, str(self.time_intv),
                                       self.prof_name, self.info_dict["capacity"])

class Discussion(object):
    """
    One of multiple discussions for a lecture. Contains information about:
    day held; TA name; discussion hours.
    """
    # 0 = name (align left), 1 = days, 2 = time_interval, 3 = ta_name
    DISC_FSTR = "DIS {0:<2s} [{1}] {2} | {3}"

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
        """
        Returns a string representing this discussion. Every item is aligned
        until the pipe (ta_name).
        """
        return Discussion.DISC_FSTR.format(self.name, self.day,
                                           str(self.time_intv), self.ta_name)
