A repository for all things UCLA.

## Projects

Besides miscellaneous scripts, this repo will occasionally be updated with
hobby projects that might be actually useful to other people. These however
are not fully documented or tested, so don't count on them being completely
error-free.

#### Crsparser

Crsparser is a library that can be used to parse the UCLA course catalog. It
accepts course listings data in the format used by the quarterly "Schedule of
Classes" UCLA distributes on the [registrar's website] (http://www.registrar.ucla.edu/).
What one can do is download the pdf, copy all the course listings text into
a file, and then use Parser to parse the data. Note that one must also supply
a list of departments before using Parser (one is included in the /data folder
for convenience).

Also included is a command-line interface `cmdui.py`, which uses the parser
to parse, filter, and display course data. Run `python main.py` to start the
program from the project directory.
