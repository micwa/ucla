A repository for all things UCLA. The \_school directory contains class-related
stuff; the other folders are repo-like folders themselves.

## Overview

Besides miscellaneous scripts, this repo will occasionally be updated with
"projects" (i.e. programs larger than one or two files) that might be of some
use to other people. They however are not fully documented or tested, so don't
count on them being completely error-free.

#### Crsparser

Crsparser is a library that can be used to parse the UCLA course catalogue for
classes and filter them using different criteria.

The parser accepts course listings data in the format used by the quarterly
"Schedule of Classes" UCLA distributes on the [registrar's website]
(http://www.registrar.ucla.edu/).  To use the parser, download the pdf, copy
all the course listings text into a file, and then use Parser to parse the
data. Note that one must also supply a list of departments before using Parser
(one is included in the /data folder for convenience).

Also included is a command-line interface `cmdui.py`, which uses the parser to
parse, filter, and display course data. If you're feeling lazy and don't want
to create a new script, run `python main.py` from the root project directory to
start the program.

### Scripts

Crsscan.py
* Scans the courses specified in load\_courses() every SCAN_INTERVAL
  minutes, and logs results to a file
* If there is an opening, sends an email notification
* TO USE:
    1. Add courses and sections to scan in `load_courses()`
    2. If using own client, create a new ScanThread to scan, or just call
       `scan_once()`
    3. Edit global variables to change sender/recipient email, scan
       interval, file directory
    4. Add a text file containing (or hardcode) username/password for email

## Author

Michael Wang, <micwa@ucla.edu>
