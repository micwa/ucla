"""
A command-line interface for crsparser.
"""

import crsparser.filter as filter
from crsparser.parse import Parser
from crsparser.util.time import Time
import crsparser.util.utils as utils

STATUS_UNLOADED = "No data loaded"
STATUS_LOADED = "Data loaded; filters added: {0}"
FILTER_NAMES = ["Duration equals",
                "Duration greater than",
                "Duration lesser than",
                "Occurs at/after",
                "Occurs at/before",
                "Starts at exactly",
                "Ends at exactly",
                "Is upper division (>=100)",
                "Is a lab (\"L\" suffix)"]

_depts = []             # List of Departments
_filters = []           # List of functions to pass to filter.filter()
_filter_names = []      # List of filter descriptions (strings)
_status = ""            # Status of program

def run():
    """Starts the program."""
    global _status
    _status = STATUS_UNLOADED

    print "\n***************"
    print "** crsparser **"
    print "***************"

    while True:
        print "\nMain menu"
        print "========="
        print "\n1. Parse data"
        print "2. Filter & display data"
        print "3. Quit"
        print "\n{0}: {1}".format("STATUS", _status)
        print "\nChoose an option:",

        option = raw_input()

        if option == "1":
            parse_data()
        elif option == "2":
            filter_data()
        elif option == "3":
            print "\nGoodbye!"
            break
        else:
            print "Error: invalid option"
            continue

def parse_data():
    """
    Prompts the user for the file containing the list of departments and the
    course listings, and parses the data.
    """
    print "\nParsing data"
    print "============\n"
    print "Use defaults of depts.txt and data.txt? (y/n)",

    option = raw_input()

    if option == "" or option[0].lower() == "y":    # Allow empty input
        dept_file = "depts.txt"
        data_file = "data.txt"
    else:
        print "\nName of file with list of departments:",
        dept_file = raw_input()
        print "Name of file with catalog data:",
        data_file = raw_input()

    # Load departments into _depts
    print "\nParsing data..."

    try:
        Parser.load_dept_list(dept_file)
        global _depts
        _depts = Parser.parse_catalog(data_file)
    except IOError, e:
        print "ERROR:", e
        print "\nPress <Enter> to continue..."
        raw_input()
        return

    print "\n...Done"
    global _status
    _status = STATUS_LOADED.format(0)

def filter_data():
    """Prompts the user to add filters, display results, or reset filters."""
    if _status == STATUS_UNLOADED:
        print "ERROR: no data loaded"
        print "\nPress <Enter> to continue..."
        raw_input()
        return

    while True:
        print "\nFilters"
        print "======="
        print "\n1. Add filter"
        print "2. Display results"
        print "3. Reset filters"
        print "4. Back"
        print "\nFilters added << " + " << ".join(_filter_names)
        print "\nChoose an option:",

        option = raw_input()

        if option == "1":
            _add_filter()
        elif option == "2":
            _display_results()
        elif option == "3":
            _reset_filters()
        elif option == "4":
            break
        else:
            print "Error: invalid option"
            continue

def _add_filter():
    global _filters, _filter_names

    while True:
        print "\nAdd a filter:"
        print "-------------"
        print "    0: [Back]"
        for i, f in enumerate(FILTER_NAMES):
            print "    {0}: {1}".format(i + 1, f)
        print "\nFilters added << " + " << ".join(_filter_names)
        print "\nChoose an option:",

        option = raw_input()
        fn = None
        name = None

        # Convert option to int
        if not utils.isint(option):
            print "Error: not a number"
            continue
        else:
            option = int(option)

        # Add appropriate filter to _filters
        if option == 0:
            break
        elif option >= 1 and option <= 3:       # Integer number of minutes
            print "Enter number of minutes:",
            mins = raw_input()

            if not utils.isint(mins):
                print "Error: invalid number of minutes"
                continue
            else:
                m = int(mins)
                fn = {
                    1: filter.duration_eq(m),
                    2: filter.duration_ge(m),
                    3: filter.duration_le(m)
                }.get(option)
                name = FILTER_NAMES[option - 1] + ": " + mins
        elif option >= 4 and option <= 7:       # A time, e.g. "9:00"
            print "Enter a time:",
            time = raw_input()

            if not utils.istime(time):
                print "Error: invalid time"
                continue
            else:
                t = Time(time)
                fn = {
                    4: filter.occurs_after(t),
                    5: filter.occurs_before(t),
                    6: filter.starts_at(t),
                    7: filter.ends_at(t)
                }.get(option)
                name = FILTER_NAMES[option - 1] + ": " + time
        elif option == 8:
            fn = filter.isupperdiv()
            name = FILTER_NAMES[option - 1]
        elif option == 9:
            fn = filter.islab()
            name = FILTER_NAMES[option - 1]
        else:
            print "Error: invalid option"
            continue

        _filters.append(fn)
        _filter_names.append(name)

def _display_results():
    for d in _depts:
        print "\n-----", str(d), "-----"
        # If no filters, print out everything
        if len(_filters) == 0:
            for c in d.courses:
                print str(c)
                for lec in c.lec_list:
                    print "   " + str(lec)
        # If filters set, filter d.courses
        else:
            selected = filter.filter(d.courses, _filters)
            for i in xrange(len(d.courses)):
                if selected[i]:
                    print str(d.courses[i])
                    for lec in d.courses[i].lec_list:
                        print "   " + str(lec)

def _reset_filters():
    global _filters, _filter_names, _status
    _filters = []
    _filter_names = []
    _status = STATUS_LOADED.format(0)
    print "\n---FILTERS RESET---"
