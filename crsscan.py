import re
import time
import threading
import urllib
import smtplib
from email.mime.text import MIMEText

SCAN_INTERVAL = 1    # Minutes between each scan
FOUND_INTERVAL = 60  # If a course is found, minutes until course is scanned again

# For email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

DATA_DIR = "_data/"
RECIP_ADDR = "crs.scan.ucla@gmail.com"      # The recipient address (for now, only one)
SENDER_FILE = DATA_DIR + "gmail.txt"        # Contains email/password info for sender
#COURSE_FILE = DATA_DIR + "courses.txt"      # List of courses

_email = None
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
    courses = {}    # Dict mapping string -> (string,[string])
    found = {}      # Dict mapping string -> int
    started = False # Whether the scan has started or not
    thr = None

    # Load courses
    load_courses(courses, found)
    
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

        if started:
            print "\n***SCANNING STARTED***"

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
            started = False
            print "Scanning stopped"
        elif option == "5":
            print "\nGoodbye!"
            if thr is not None:
                thr.stop()
                thr.join()
            break
        else:
            print "\nInvalid option."

def load_courses(courses, found):
    courses["Anthro 9"] = ("http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15W&subareasel=ANTHRO&idxcrs=0009++++",
                           ["1A", "1B", "1C", "1D", "1E", "1F"])
    courses["Math 32B"] = ("http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15W&subareasel=MATH&idxcrs=0032B+++",
                           ["3A", "3B", "3C", "3D", "3E", "3F"])
    courses["Math 33A"] = ("http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15W&subareasel=MATH&idxcrs=0033A+++",
                           ["1A", "1B", "1C", "1D", "1E", "1F"])
    courses["Physics 1B"] = ("http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15W&subareasel=PHYSICS&idxcrs=0001B+++",
                             ["1A", "1B", "1C", "1D", "1E"])
    courses["Physics 1C"] = ("http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15W&subareasel=PHYSICS&idxcrs=0001C+++",
                             ["1A", "1B", "1C", "1D", "1E"])

    # Set all found[course] to 0
    for name in courses.keys():
        found[name] = 0

def add_course(courses, found):
    """Prompts for a course to add."""
    print "\nAdd a course"
    print "------------"
    print "Course name:",
    name = raw_input()
    print "URL:",
    url = raw_input()

    # Parse sections
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

    courses[name] = (name, sec_list)
    found[name] = 0

def show_courses(courses):
    """Prints the list of courses to screen."""
    print "\n---Added courses---\n"
    for name, data in courses.iteritems():
        print "{0:<12}: {1}".format(name, ", ".join(data[1]))

def scan_once(courses, found, outfile):
    """
    Scans courses (a dict), where courses[string] = (url,[sections]).
    If a course section is available, notifies the user and sets found[course]
    to FOUND_INTERVAL.
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
            outfile.write("*****ERROR scanning course.\n")
            continue
        
        for i in xrange(len(data[1])):
            # Section is open; note that if multiple sections are open, user_notify()
            # is called multiple times
            if tuples[i][0] < tuples[i][1]:
                msg = ("***Section {0} is open! {1} out of {2} spot taken\n"
                       .format(data[1][i], tuples[i][0], tuples[i][1]))
                outfile.write(msg)
                found[name] = FOUND_INTERVAL

                if user_notify(name, msg):
                    outfile.write("+++Email sent to {0}\n".format(RECIP_ADDR))
                else:
                    outfile.write("*****ERROR: failed to send email to {0}\n".format(RECIP_ADDR))
            else:
                # Closed message is more concise
                outfile.write("*{0}: {1}/{2}\n"
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
    """
    Notifies the RECIP_ADDR about the course being opened, sending them the given message.
    Returns true if the mail was sent successfully, and false otherwise.
    """
    global _email, _password

    # Assume first line is email, second is password
    if _email is None and _password is None:
        with open(SENDER_FILE) as passfile:
            _email = passfile.readline().strip()
            _password = passfile.readline().strip()

    # Create message, then connect to SMTP server
    msg = MIMEText(msg)
    msg["From"] = _email
    msg["To"] = RECIP_ADDR
    msg["Subject"] = "{0} is open!".format(course)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    # server.set_debuglevel(True)

    try:
        server.starttls()
        server.login(_email, _password)
        server.sendmail(_email, [RECIP_ADDR], msg.as_string())
    except smtplib.SMTPException:
        return False
    finally:
        server.quit()

    return True

if __name__ == "__main__":
    run()