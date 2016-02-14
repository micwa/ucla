"""
A command-line operated course scanner, configured to scan the UCLA course
listings on www.registrar.ucla.edu.

Copyright (C) 2014, 2016 by Michael Wang
"""

import getpass
import re
import smtplib
import sys
import threading
import time
import urllib
from email.mime.text import MIMEText

# CONFIGURABLE VARIABLES
SCAN_INTERVAL = 1               # Minutes between each scan
SMTP_SERVER = "smtp.gmail.com"  # For email
SMTP_PORT = 587
RECIP_ADDR = "crs.scan.ucla@gmail.com"      # The recipient address
SMS_ADDR = "xxxaaa1234@txt.att.net"         # To use, change the domain to your carrier's

# If empty, the program will prompt you for these at startup
_email = None
_password = None

class ScanThread(threading.Thread):
    """
    A thread that runs scan_once() every SCAN_INTERVAL minutes with
    the specified courses and a log file.
    """
    def __init__(self, courses, log_file):
        threading.Thread.__init__(self)
        self.courses = courses
        self.log_file = log_file
        self.do_run = True
        self.event = threading.Event()      # To interrupt wait() later
        self.daemon = True

    def run(self):
        with open(self.log_file, "w") as outfile:
            while self.do_run:
                t = time.time()
                scan_once(self.courses, outfile)
                outfile.flush()
                elapsed = time.time() - t   # So time between intervals is consistent
                self.event.wait(SCAN_INTERVAL * 60 - elapsed)

    def stop(self):
        self.event.set()
        self.do_run = False

class Course(object):
    """
    A course to scan, which stores enrollment information.
    """
    def __init__(self, name, url, sections):
        self.name = name
        self.url = url
        self.sections = sections
        
        self._tups = None       # Dict to store section enrollment tuples

    def update(self, tuples):
        """
        Updates this course's enrollment information. Returns a list of 4-tuples
        (section, type, filled, capacity) for each newly opened course, where
        type is either 'E' (enroll) or 'W' (waitlist).
        This solves the problem of continually receiving notifications for the
        same opened class without having a notification delay (which could make
        you miss a notification in that time). But it is possible that, in a
        small time frame, someone enrolls in a course and another person immediately
        drops the same course, you will not be notified of the event. With the
        slow update time of UCLA's servers, however, this is not much of a problem.
        
        tuples - a list of 4-tuples of the enrollment numbers of the
                 corresponding sections
        """
        open = []
        if not self._tups:
            self._tups = {}
            for sec, tup in zip(self.sections, tuples):
                self._tups[sec] = tup
                if tup[0] < tup[1]:
                    open.append((sec, 'E', tup[0], tup[1]))
                elif tup[2] < tup[3]:
                    open.append((sec, 'W', tup[2], tup[3]))
            return open

        # Getting here means the course has been updated at least once already.
        # Assume that enrollment/waitlist capacities are constant.
        for sec, tup in zip(self.sections, tuples):
            prev = self._tups[sec]
            
            # Only consider just opened courses as "open"
            if prev[0] == prev[1] and tup[0] < tup[1]:
                open.append((sec, 'E', tup[0], tup[1]))
            elif prev[2] == prev[3] and tup[2] < tup[3]:
                open.append((sec, 'W', tup[2], tup[3]))
                
            self._tups[sec] = tup
        return open


def run():
    courses = []    # List of Courses
    started = False # Whether the scan has started or not
    thr = None

    # If email/password is not specified, prompt for them
    global _email, _password
    if not _email and not _password:
        print "Enter your email information"
        _email, _password = prompt_for_email()

    # Load courses
    load_courses(courses)
    
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
            print "\n***SCAN IN PROGRESS***"

        print "\nChoose an option:",
        option = raw_input()

        if option == "1":
            add_course(courses)
        elif option == "2":
            show_courses(courses)
        elif option == "3":
            if started:
                print "\nERROR: scanning has already started."
            else:
                thr = ScanThread(courses, "scan.log")
                thr.start()
                started = True
                print "\nStarting scan..."
        elif option == "4":
            if not started:
                print "\nERROR: scanning has not been started"
            else:
                thr.stop()           # Must stop (i.e. interrupt), then wait for it to finish
                thr.join()           # or else the thread holds onto the file
                started = False
                print "Scanning stopped"
        elif option == "5":
            print "\nGoodbye!"
            sys.exit()
        else:
            print "\nInvalid option."

def prompt_for_email():
    """Prompts for an email and a password. Returns a tuple (email, password)."""
    print "Email (user@email.com):",
    email = raw_input()
    password = getpass.getpass("Password: ")

    return (email, password)

def load_courses(courses):
    """
    SPECIFY YOUR COURSES TO SCAN HERE.
    Each course should be a Course object constructed with three arguments:
        course name - name of the course
        course page url - url of the course page to scan
        section list - list of sections to watch for
    """
    courses.append(Course("Math 33B",
                          "http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15S&subareasel=MATH&idxcrs=0033B+++",
                          ["1A", "1B", "1C", "1D", "1E", "1F", "2A", "2B", "2C", "2D", "2E", "2F"]))
    courses.append(Course("CS M51A",
                          "http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15S&subareasel=COM+SCI&idxcrs=0051A+M+",
                          ["1A", "1B"]))
    #courses.append(Course("Math 61",
    #                      "http://www.registrar.ucla.edu/schedule/detselect.aspx?termsel=15S&subareasel=MATH&idxcrs=0061++++",
    #                      ["1A"]))

def add_course(courses):
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
        sections = sections.split(",")

        try:
            for sec in sections:
                sec = sec.strip()
                if len(sec) == 1 and not sec[0].isdigit():
                    raise ValueError()
                elif len(sec) == 2 and (not sec[0].isdigit() or not sec[1].isalpha()):
                    raise ValueError()
                elif len(sec) > 2:
                    raise ValueError()

                sec_list.append(sec.upper())
        except ValueError:
            print "***Invalid format for sections."
            sec_list = []
        else:
            break
    
    courses.append(Course(name, url, sec_list))

def show_courses(courses):
    """Prints the list of courses to the screen."""
    print "\n---Added courses---\n"
    for crs in courses:
        print "{0:<12}: {1}".format(crs.name, ", ".join(crs.sections))

def scan_once(courses, outfile):
    """
    Scans courses (a list of Courses) and updates each Course with a new 4-tuple,
    after which the Course can decide whether or not to notify the user.
    """

    t = time.strftime("%d-%b-%y %H:%M:%S", time.localtime())
    outfile.write("\nNew scan at: {0}\n".format(t))
    outfile.write("-----------------------------------")
    
    for crs in courses:
        outfile.write("\nScanning {0}...\n".format(crs.name))
        try:
            tuples = _scan_course(crs.name, crs.url, crs.sections)
        except:
            outfile.write("*****ERROR scanning course.\n")
            continue

        # Update all courses
        open = crs.update(tuples)
        
        if not open:
            for sec, tup in zip(crs.sections, tuples):
                outfile.write("*{0}: {1}/{2}, {3}/{4}\n"
                              .format(sec, tup[0], tup[1], tup[2], tup[3]))
            continue
        
        # Don't write any closed messages if there are sections open
        for sec, ch, en, encp in open:
            if ch == "E":
                msg = ("***Section {0} is open! {1} out of {2} spots taken\n"
                       .format(sec, en, encp))
            else:
                msg = ("***Section {0}'s WAITLIST is open! {1} out of {2} spots taken\n"
                       .format(sec, en, encp))
            outfile.write(msg)
            
            if user_notify(crs.name, msg):
                outfile.write("+++Email sent to {0}\n".format(RECIP_ADDR))
            else:
                outfile.write("*****ERROR: failed to send email to {0}\n".format(RECIP_ADDR))


def _scan_course(name, url, sections):
    """
    Scans a course with given name at the url, considering only the specified sections.
    Returns list of 4-tuples in the format: (enrolled, enroll_capacity, waitlist, waitlist_capacity).
    """
    # Open url
    url = urllib.urlopen(url)
    lines = url.readlines()

    # Names to look for
    SEC_NUMBER = "SectionNumber"
    VAL_LIST = ["_EnrollTotal", "_EnrollCap", "_WaitListTotal", "_WaitListCap"]
    
    regex_dict = {}      # Simple regexes
    for item in VAL_LIST:
        regex_dict[item] = item + r"[^0-9]*([0-9]+)"
    results = [0, 0, 0, 0]
    i = 0

    tuples = []          # Each tuple corresponds to the (En, EnCp, Wl, WlCp) of each section
    for sec in sections:
        while i < len(lines):
            if SEC_NUMBER in lines[i] and (">" + sec + "<") in lines[i]:
                break
            i += 1
        for n, item in enumerate(VAL_LIST):         # Search for each value
            while i < len(lines):
                if item in lines[i]:
                    r = re.search(regex_dict[item], lines[i])
                    results[n] = int(r.group(1))    # No longer using (P?<name>)
                    break
                i += 1
        tuples.append(tuple(results))

    return tuples

def user_notify(course, msg):
    """
    Notifies the RECIP_ADDR about the course being opened, sending them the given message.
    Returns true if the mail was sent successfully, and false otherwise.
    """
    # Create message, then connect to SMTP server
    msg = MIMEText(msg)
    msg["From"] = _email
    msg["To"] = RECIP_ADDR
    msg["Subject"] = "{0} is open!".format(course)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

    try:
        server.starttls()
        server.login(_email, _password)

        # Send to both emails at once
        server.sendmail(_email, [RECIP_ADDR, SMS_ADDR], msg.as_string())
    except smtplib.SMTPException:
        return False
    finally:
        server.quit()

    return True

if __name__ == "__main__":
    run()
