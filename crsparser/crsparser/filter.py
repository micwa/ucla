"""
Provides the capability to filter Courses from a Catalog (i.e. select courses
with certain criteria). To assist with filtering, this module contains
functions that return functions f: Course, *args -> bool that wrap functions
in Course (because filter() expects that type of function).
"""

def filter(courses, *args):
    """
    Arguments:
    
    courses - list of courses to filter
    *fns - list of tuples, where the first element is a function 
           f: Course, *args -> bool and the other elements are its arguments
    """
    for crs in courses:
        for tup in args:
            if not tup[0](cl, list(t[1:])):
                # Mark course as uninteresting, then proceed to process next course
                break
    # Do something with (display) the courses remaining

def duration_eq(n):
    """
    Returns a function that returns true if the Course's duration is exactly
    equal to n.
    """
    return lambda crs, *args: crs.duration() == n

def duration_ge(n, *args):
    """
    Returns a function that returns true if the Course's duration is greater
    than or equal to n.
    """
    return lambda crs, *args: crs.duration() >= n

def duration_le(n, *args):
    """
    Returns a function that returns true if the Course's duration is less
    than or equal to n.
    """
    return lambda crs, *args: crs.duration() <= n

def islab():
    """Returns a function that returns true if the Course is a lab."""
    return lambda crs, *args: crs.islab()
    
def islab():
    """Returns a function that returns true if the Course is an upper division course."""
    return lambda crs, *args: crs.isupperdiv()

def starts_at(time):
    """
    Returns a function that returns true if the Course has a Lecture that
    starts at the specified time (Time object).
    """
    return lambda crs, *args: crs.starts_at(args[0])

def ends_at(time):
    """
    Returns a function that returns true if the Course has a Lecture that
    ends at the specified time (Time object).
    """
    return lambda crs, *args: crs.ends_at(args[0])
