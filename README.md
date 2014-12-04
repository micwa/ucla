A repository for all things UCLA. The _school directory contains class-related
stuff; all the other folders are repo-like folders themselves.

### Projects

Besides miscellaneous scripts, this repo will occasionally be updated with
"projects" (i.e. programs larger than one or two files) that might be of some
use to other people. They however are not fully documented or tested, so don't
count on them being *completely* error-free.

#### Crsparser

Crsparser is a library that can be used to parse the UCLA course catalog for
classes and filter them using different criteria. The filtering is implemented
using function variables and lambdas wrapping functions taking varying numbers
of arguments (see filter.py more details).

The parser accepts course listings data in the format used by the quarterly
"Schedule of Classes" UCLA distributes on the
[registrar's website] (http://www.registrar.ucla.edu/).
To use the parser, download the pdf, copy all the course listings text into
a file, and then use Parser to parse the data. Note that one must also supply
a list of departments before using Parser (one is included in the /data folder
for convenience).

Also included is a command-line interface `cmdui.py`, which uses the parser
to parse, filter, and display course data. If you're feeling lazy and don't
want to create a new script, run `python main.py` from the root project
directory to start the program.
