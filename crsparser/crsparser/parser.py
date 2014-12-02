import re
from course import Department, Course, Lecture, Discussion
from util.time import Time, TimeInterval

class Parser:
    """
    Class that allows users to parse the course catalog. All methods are
    class methods; there is no need to instantiate any Parser objects.
    """
    # Matches one course single course (one line)
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
        file = open(filename)
        lines = file.readlines()
        for ln in lines:
            Parser.dept_list.append(ln.strip())

        file.close()

    @staticmethod
    def parse_single_course(line):
        r = re.match(Parser.COURSE_REGEX, line)
        print r.groups()

    @staticmethod
    def parse_single_subcourse(line):
        r = re.match(Parser.SUB_COURSE_REGEX, line)
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
            
        file = open(filename)
        depts = []
        
        # Temp variables
        line = file.readline().strip()
        lines = []
        Parser.dept_list.append("\x00\x01\x02")  # So dept_list[i+1] doesn't raise an error
        Parser.dept_list.append("\x00\x01\x02")
        n = len(Parser.dept_list) - 2            # "Real" length of dept_list
        i = 0

        # Set up first department match
        # Look ahead only one department if the current department does not exist
        while (i < n and line != "" and line != Parser.dept_list[i] and
                         line != Parser.dept_list[i+1]):
            line = file.readline().strip()

        # Account for look-ahead
        if i + 1 < n and line == Parser.dept_list[i+1]:
            print "Skipped over:", Parser.dept_list[i]
            i += 1

        while i < n and line != "":
            # Get all lines before next department name
            line = file.readline()
            i += 1
            if i > n:
                break
            
            while (line != "" and line != Parser.dept_list[i] and
                   line != Parser.dept_list[i+1]):
                lines.append(line)
                line = file.readline().strip()

            if i + 1 < n and line == Parser.dept_list[i+1]:
                print "Skipped over:", Parser.dept_list[i]
                i += 1
                
            # Parse all lines in department
            d = Parser.parse_dept(Parser.dept_list[i - 1], lines)
            depts.append(d)
            lines = []

        Parser.dept_list.pop()
        Parser.dept_list.pop()
        file.close()
        
        return depts

    @staticmethod
    def parse_course(lines):
        lec_list = []
        disc_list = []                      # Temporary variable

        # First lecture
        r = re.match(Parser.COURSE_REGEX, lines[0])
        name = r.group("name")
        number = r.group("number")

        sec_num = r.group("sec_num")
        days = r.group("days")
        time_start = r.group("time_start")
        time_end = r.group("time_end")
        loc = r.group("loc")
        prof = r.group("prof")
        capac = r.group("capac")
        xc = r.group("xc")
        grade_type = r.group("grade_type")
        units = r.group("units")
        
        lec = Lecture(sec_num, days, prof, TimeInterval(time_start, time_end),
                      capac, disc_list)
        lec_list.append(lec)

        # Rest of lines
        for ln in lines:
            r = re.match(Parser.SUB_COURSE_REGEX, ln)
            if r is not None:
                sec_num = r.group("sec_num")
                days = r.group("days")
                time_start = r.group("time_start")
                time_end = r.group("time_end")
                loc = r.group("loc")
                prof = r.group("prof")
                capac = r.group("capac")
                xc = r.group("xc")
                grade_type = r.group("grade_type")
                units = r.group("units")
                
                lec = Lecture(sec_num, days, prof, TimeInterval(time_start, time_end),
                              capac, disc_list)
                lec_list.append(lec)
        
        return Course(name, number, lec_list, blah="blah")
            
    @staticmethod
    def parse_dept(dept, lines):
        print "\n-----" + dept + "-----"
        courses = []

        # Temp variables
        lns = []
        i = 0

        # Set up first class match
        while i < len(lines) and not re.match(Parser.COURSE_REGEX, lines[i]):
            i += 1
        
        while i < len(lines):
            r = re.match(Parser.COURSE_REGEX, lines[i])
            lns.append(lines[i])
            i += 1

            # Get all lectures in class (loop until next course match)
            while i < len(lines) and not re.match(Parser.COURSE_REGEX, lines[i]):
                lns.append(lines[i])
                i += 1

            c = Parser.parse_course(lns)
            courses.append(c)
            lns = []

        return Department(dept, courses)
