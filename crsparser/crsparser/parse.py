import re
from crsparser.course import Department, Course, Lecture
import crsparser.util.utils as utils
from crsparser.util.time import Time, TimeInterval

class Parser(object):
    """
    Class that allows users to parse the course catalog. All methods are
    class methods; there is no need to instantiate any Parser objects.
    """
    # Matches course title (e.g. 100 COURSE TITLE Y)
    COURSE_TITLE_REGEX = \
            (r"(?P<number>\w+\b)\s+"         # Catalog number
             r"(?P<name>.+)\s+(Y|N)\s+")     # Class name; must trim trailing whitespace

    # Matches a lecture, starting optionally with a Y/N
    COURSE_LEC_REGEX = \
            (r"(Y|N)?\s*"
             r"((?P<dashes>-+)|"
             r"(?P<lec_id>[0-9]{3}-[0-9]{3}-[0-9]{3}))\s+"
             r"(?P<class_type>\w+)\s+"              # Class type, e.g. LEC or SEM
             r"(?P<sec_num>[0-9][a-zA-Z]?)\s+"      # Section number
             r"(?P<days>\w+)\s+"                    # Days held
             r"(?P<time_start>" + Time.TIME_REGEX + r")\s*-\s*" # Time start
             r"(?P<time_end>" + Time.TIME_REGEX + r")\s+"       # Time end
             r"(?P<loc>[^0-9]+[0-9]+[a-zA-z]*)?\s*" # Optional: Location (depends on number at end)
             r"(?P<prof>[^0-9]*)?\s*"               # Optional: Professor name
             r"(?P<capac>[0-9]+)\s+"                # Enrollment capacity
             r"(?P<xc>[0-9]+)\s+"                   # Exam code
             r"(?P<grade_type>[a-zA-Z]+)\s+"        # Grade type
             r"(?P<units>[0-9])\.")                 # Number of units (< 10)

    # Full line
    COURSE_ALL_REGEX = COURSE_TITLE_REGEX + COURSE_LEC_REGEX

    # List of all departments, in the order they will be encountered
    # in the listings (for UCLA, it's alphabetical).
    dept_list = []

    def __init__(self):
        raise RuntimeError("What do you think you're doing?")

    @staticmethod
    def load_dept_list(filename):
        """
        Loads the department names from the file with the given filename. Expects
        each line in the file to be a single department name.
        Note that parse_catalog assumes that the department name in the data file
        is *exactly* the same as in the department file (i.e. case sensitive, though
        whitespace is stripped).
        """
        with open(filename) as f:
            lines = f.readlines()
            for ln in lines:
                Parser.dept_list.append(ln.strip())

    @staticmethod
    def parse_single_course(line):
        r = re.match(Parser.COURSE_ALL_REGEX, line)
        print r.groups()

    @staticmethod
    def parse_single_subcourse(line):
        r = re.match(Parser.COURSE_LEC_REGEX, line)
        print r.groups()

    @staticmethod
    def parse_catalog(filename):
        """
        Parses the course listings in the given file (represented by the filename)
        and returns a list of all the departments, which each contain a list of
        classes. The user must call Parser.load_dept_list() with the proper
        department names or else this function raises an error.
        """
        if Parser.dept_list == []:
            raise RuntimeError("List of departments is empty.")

        infile = open(filename)
        depts = []

        # Temp variables
        line = infile.readline().strip()
        lines = []
        Parser.dept_list.append("\x00\x01\x02")  # So dept_list[i+1] doesn't raise an error
        Parser.dept_list.append("\x00\x01\x02")
        n = len(Parser.dept_list) - 2            # "Real" length of dept_list
        i = 0

        # Set up first department match
        # Look ahead only one department if the current department does not exist
        while (i < n and line != "" and line != Parser.dept_list[i] and
               line != Parser.dept_list[i+1]):
            line = infile.readline().strip()

        # Account for look-ahead
        if i + 1 < n and line == Parser.dept_list[i+1]:
            print "Skipped over:", Parser.dept_list[i]
            i += 1

        while i < n and line != "":
            # Get all lines before next department name
            line = infile.readline()
            i += 1
            if i > n:
                break

            while (line != "" and line != Parser.dept_list[i] and
                   line != Parser.dept_list[i+1]):
                lines.append(line)
                line = infile.readline().strip()

            if i + 1 < n and line == Parser.dept_list[i+1]:
                print "Skipped over:", Parser.dept_list[i]
                i += 1

            # Parse all lines in department
            d = Parser.parse_dept(Parser.dept_list[i - 1], lines)
            depts.append(d)
            lines = []

        Parser.dept_list.pop()
        Parser.dept_list.pop()
        infile.close()

        return depts

    @staticmethod
    def parse_course(lines):
        lec_list = []

        # Temporary variables
        disc_list = []
        info_dict = {}

        # First lecture
        r = re.match(Parser.COURSE_TITLE_REGEX, lines[0])
        name = r.group("name").strip()
        number = r.group("number")

        # Rest of lectures
        for ln in lines:
            r = re.search(Parser.COURSE_LEC_REGEX, ln)
            if r is not None:
                # Same as above
                sec_num = r.group("sec_num")
                days = r.group("days")
                time_start = r.group("time_start")
                time_end = r.group("time_end")
                loc = r.group("loc")
                prof = r.group("prof").strip()

                capac = r.group("capac")
                xc = r.group("xc")
                grade_type = r.group("grade_type")
                units = r.group("units")
                info_dict[Lecture.INFO_KEYS[0]] = loc
                info_dict[Lecture.INFO_KEYS[1]] = capac
                info_dict[Lecture.INFO_KEYS[2]] = xc
                info_dict[Lecture.INFO_KEYS[3]] = grade_type
                info_dict[Lecture.INFO_KEYS[4]] = units

                h = utils.stoi(time_start)  # Since time_start does not have a suffix, add one if in afternoon
                if h / 100 < 8:
                    time_start += "p"

                lec = Lecture(sec_num, days, prof, TimeInterval(time_start, time_end),
                              info_dict, disc_list)
                lec_list.append(lec)

        return Course(name, number, lec_list)

    @staticmethod
    def parse_dept(dept, lines):
        courses = []

        # Temp variables
        lns = []
        i = 0

        # Set up first class match
        while i < len(lines) and not re.match(Parser.COURSE_ALL_REGEX, lines[i]):
            i += 1

        while i < len(lines):
            lns.append(lines[i])
            i += 1

            # Get all lectures in class (loop until next course match)
            while i < len(lines) and not re.match(Parser.COURSE_ALL_REGEX, lines[i]):
                lns.append(lines[i])
                i += 1

            c = Parser.parse_course(lns)
            courses.append(c)
            lns = []

        return Department(dept, courses)
