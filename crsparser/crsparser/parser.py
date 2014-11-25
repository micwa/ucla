import re
import course
from util.time import Time, TimeInterval
from util.misc import stoi

class Parser:
    """
    Class that allows users to parse the course catalog. All methods are
    class methods; there is no need to instantiate any Parser objects.
    """
    # Group 1 = dept name (all capitals); assume that a newline follows the name
    DEPT_REGEX = r"((?:[A-Z-/]+(?:\s+|$))+)$"
    
    COURSE_REGEX = (r"(?P<number>\w+\b)\s+"              # Catalog number
                    r"(?P<name>.+)(Y|N)\s+(Y|N)?\s*"     # Class name; must trim trailing whitespace
                    r"((?P<dashes>-+)|"                  # Dashes, if no id
                    r"(?P<lec_id>[0-9]{3}-[0-9]{3}-[0-9]{3}))\s+"    # ID to enroll
                    r"(?P<class_type>\w+)\s+"            # Class type, e.g. LEC or SEM
                    r"(?P<sec_num>[0-9][a-zA-Z]?)\s+"    # Section number
                    r"(?P<days>\w+)\s+"                  # Days held
                    r"(?P<time_start>" + Time.TIME_REGEX + ")\s*-\s*"   # Time start
                    r"(?P<time_end>" + Time.TIME_REGEX + ")\s+"      # Time end
                    r"(?P<loc>[^0-9]+[0-9]+[a-zA-z]*)\s+"    # Location (depends on number at end)
                    r"(?P<prof>[^0-9]*)\s+"              # Professor name
                    r"(?P<capac>[0-9]+)\s+"              # Enrollment capacity
                    r"(?P<xc>[0-9]+)\s+"                 # Exam code
                    r"(?P<grade_type>[a-zA-Z]+)\s+"      # Grade type
                    r"(?P<units>[0-9])\.")               # Number of units (< 10)

    # Same as COURSE_REGEX, except for lectures in the same class after
    # the first one; starts at "Y?".
    SUB_COURSE_REGEX = ("(Y|N)?\s*"
                        r"((?P<dashes>-+)|"
                        r"(?P<lec_id>[0-9]{3}-[0-9]{3}-[0-9]{3}))\s+"
                        r"(?P<class_type>\w+)\s+"
                        r"(?P<sec_num>[0-9][a-zA-Z]?)\s+"
                        r"(?P<days>\w+)\s+"
                        r"(?P<time_start>" + Time.TIME_REGEX + ")\s*-\s*"
                        r"(?P<time_end>" + Time.TIME_REGEX + ")\s+"
                        r"(?P<loc>[^0-9]+[0-9]+[a-zA-z]*)\s+"
                        r"(?P<prof>[^0-9]*)\s+"
                        r"(?P<capac>[0-9]+)\s+"
                        r"(?P<xc>[0-9]+)\s+"
                        r"(?P<grade_type>[a-zA-Z]+)\s+"
                        r"(?P<units>[0-9])\.")

    SAME_AS_REGEX = r"(?P<same_as>SAME AS:.+)"
    RESTRICT_REGEX = r"(?P<restrict>RESTRICT:.+)"
    
    def __init__(self):
        raise RuntimeError("What do you think you're doing?")

    @staticmethod
    def parse_single_course(listing):
        r = re.match(Parser.COURSE_REGEX, listing)
        print r.groups()

    @staticmethod
    def parse_single_subcourse(listing):
        r = re.match(Parser.SUB_COURSE_REGEX, listing)
        print r.groups()

    @staticmethod
    def parse_catalog(filename):
        """
        Parses the course listings in the given file (represented by the filename)
        and returns a list of all the classes.
        """
        file = open(filename)
        line = file.readline()
        lines = []

        # Set up first department match
        while not re.match(Parser.DEPT_REGEX, line) and line != "":
            line = file.readline()

        while line != "":
            r = re.match(Parser.DEPT_REGEX, line)
            dept = r.group(0).strip()        # Current department
            print "\n-----" + dept + "-----"

            # Get all lines before next department name
            line = file.readline()
            while line != "" and (not re.match(Parser.DEPT_REGEX, line) or \
                  "CATALOG" in line or "STUDENT" in line or "MAJORS" in line or \
                  "MINORS" in line or "SENIOR" in line or "JUNIOR" in line or \
                  len(line) > 50):
                lines.append(line)
                line = file.readline()

            # Parse all lines in department
            Parser.parse_dept(dept, lines)
            lines = []
            
    @staticmethod
    def parse_dept(dept, lines):
        i = 0

        # Set up first class match
        while i < len(lines) and not re.match(Parser.COURSE_REGEX, lines[i]):
            i += 1
        
        while i < len(lines):
            r = re.match(Parser.COURSE_REGEX, lines[i])
            i += 1
            
            # Extract class properties to pass to parse_class()
            name = r.group("name")
            time_start = r.group("time_start")
            time_end = r.group("time_end")
            number = r.group("number")
            days = r.group("days")
            prof = r.group("prof")
            capac = r.group("capac")
            
            if 1==1: # time_start == "10:00" and stoi(number) < 100:
                print number, "|", name, "|", time_start + "-" + time_end, "|", \
                      days, "|", prof, "|", capac

            # Get all lectures in class (loop until next course match)
            while i < len(lines) and not re.match(Parser.COURSE_REGEX, lines[i]):
                r = re.match(Parser.SUB_COURSE_REGEX, lines[i])

                if r is not None:
                    time_start = r.group("time_start")
                    time_end = r.group("time_end")
                    prof = r.group("prof")
                    if 1 == 1: # time_start == "10:00" and stoi(number) < 100:
                        print "   " + number, "|", name, "|", time_start + "-" + time_end, "|", \
                              days, "|", prof, "|", capac

                i += 1
