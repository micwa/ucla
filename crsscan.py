import urllib
import re
import time
import threading

SCAN_INTERVAL = 1    # Minutes between each scan
FOUND_INTERVAL = 2  # If a course is found, minutes until course is scanned again

PASS_FILE = "_data/gmail.txt"
_user = None
_password = None

class ScanThread(threading.Thread):
    """
    A thread that runs scan_once() every SCAN_INTERVAL minutes with
    the specified courses, found, and log file.
    """
    
    def __init__(self, courses, found, log_file):
        threading.Thread.__init__(self)
        self.courses = courses
        self.found = found
        self.log_file = log_file
        self.do_run = True
        self.event = threading.Event()       # So join() will interrupt wait()

    def run(self):
        with open(self.log_file, "w") as outfile:
            while self.do_run:
                scan_once(self.courses, self.found, outfile)
                outfile.flush()
                self.event.wait(SCAN_INTERVAL * 60)

    def stop(self):
        self.event.set()
        self.do_run = False

def run():
    courses = {}    # Dict mapping string -> [string,[string]]
    found = {}      # Dict mapping string -> int
    started = False # Whether the scan has started or not
    thr = None
    
    courses["Physics 1B"] = ["http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15W&subareasel=PHYSICS&idxcrs=0001B+++",
                             ["1A", "1B", "1D"]]
    found["Physics 1B"] = 0
    courses["Physics 11"] = ["http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15W&subareasel=PHYSICS&idxcrs=0011++++",
                             ["1A", "1B"]]
    found["Physics 11"] = 1

    print "******************"
    print "* Course Scanner *"
    print "******************"

    while True:
        print "\nMain menu"
        print "---------"
        print "\n1. Add a course"
        print "2. Show added courses"
        print "3. Start scanning"
        print "4. Stop scanning"
        print "5. Quit"

        print "\nChoose an option:",
        option = raw_input()

        if option == "1":
            add_course(courses, found)
        elif option == "2":
            show_courses(courses)
        elif option == "3":
            if started:
                print "\nERROR: scanning has already started."
            else:
                thr = ScanThread(courses, found, "scan.log")
                thr.start()
                started = True
                print "\nStarting scan..."
        elif option == "4":
            thr.stop()           # Must stop (and interrupt), then wait for it to finish
            thr.join()           # or else the thread holds onto the file
            start = False
            print "Scanning stopped"
        elif option == "5":
            print "\nGoodbye!"
            if thr is not None:
                thr.stop()
                thr.join()
            break
        else:
            print "\nInvalid option."

def add_course(courses, found):
    """Prompts for a course to add."""
    print "\nAdd a course"
    print "------------"
    print "Course name:",
    name = raw_input()
    print "URL:",
    url = raw_input()

    sec_list = []
    while True:
        print "Sections (comma-separated):",
        sections = raw_input()
        sections = [c.upper() for c in sections if c.isalnum()]

        try:
            # Go two chars at a time
            for i in xrange(0, len(sections), 2):
                if sections[i].isdigit() and sections[i+1].isalpha():
                    sec_list.append(sections[i] + sections[i+1])
                else:
                    raise ValueError("Invalid format")
        except (ValueError, IndexError):
            print "Invalid format for sections."
        else:
            break

    courses[name] = [name, sec_list]
    found[name] = 0

def show_courses(courses):
    """Prints the list of courses to screen."""
    print "\n---Added courses---\n"
    for name, data in courses.iteritems():
        print "{0}: {1}".format(name, ", ".join(data[1]))

def scan_once(courses, found, outfile):
    """
    Scans courses (a dict), where courses[string] = [url,[sections]].
    If a course section is available, sets found[course] to FOUND_INTERVAL.
    """

    t = time.ctime(time.time())
    t = t[t.find(" ") + 1:t.rfind(":")]
    outfile.write("\nBeginning new scan at: {0}\n".format(t))
    outfile.write("-----------------------------------")
    
    for name, data in courses.iteritems():
        # Don't scan if already found
        if found[name] > 1:
            found[name] -= 1
            outfile.write("\n(Skipping {0})\n".format(name))
            continue

        outfile.write("\nScanning {0}...\n".format(name))
        try:
            tuples = _scan_course(name, data[0], data[1])
        except:
            outfile.write("ERROR scanning course.\n")
            continue
        
        for i in xrange(len(data[1])):
            # Section is open
            if tuples[i][0] != tuples[i][1]:
                msg = ("***Section {0} is open! {1} out of {2} spot taken\n"
                       .format(data[1][i], tuples[i][0], tuples[i][1]))
                outfile.write(msg)

                user_notify(name, msg)
                found[name] = FOUND_INTERVAL
            else:
                outfile.write("*Section {0} is closed ({1}/{2})\n"
                              .format(data[1][i], tuples[i][0], tuples[i][1]))

def _scan_course(name, url, sections):
    """
    Scans a course with given name at the url, considering only the
    specified sections.
    """
    # Open url
    url = urllib.urlopen(url)
    lines = url.readlines()

    # Constants, and temporary variables
    SEC_NUMBER = "SectionNumber"
    EN_TOTAL = "_EnrollTotal"
    EN_CAP = "_EnrollCap"
    EN_TOTAL_REGEX = EN_TOTAL + r"[^0-9]*(?P<en_total>[0-9]+)"
    EN_CAP_REGEX = EN_CAP + r"[^0-9]*(?P<en_cap>[0-9]+)"
    curr_total = 0
    curr_cap = 0
    i = 0

    tuples = []          # Each tuple corresponds to the (En, EnCp) of each section
    for sec in sections:
        while i < len(lines):
            if SEC_NUMBER in lines[i] and sec in lines[i]:
                break
            i += 1
        while i < len(lines):
            if EN_TOTAL in lines[i]:
                r = re.search(EN_TOTAL_REGEX, lines[i])
                curr_total = int(r.group("en_total"))
                break
            i += 1
        while i < len(lines):
            if EN_CAP in lines[i]:
                r = re.search(EN_CAP_REGEX, lines[i])
                curr_cap = int(r.group("en_cap"))
                break
            i += 1
        tuples.append((curr_total, curr_cap))

    return tuples

def user_notify(course, msg):
    pass

if __name__ == "__main__":
    run()
