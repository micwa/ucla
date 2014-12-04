"""
Provides the capability to filter Courses from a Catalog (i.e. select courses
with certain criteria). To assist with filtering, this module contains
functions that return functions f: Course -> bool that wrap functions
in Course (because filter() expects functions with only one argument).
"""

def filter(courses, fn_list):
    """
    Returns a list of booleans indicating whether the corresponding course
    in courses meets the criteria specified in args.

    Arguments:

    courses - list of courses to filter
    fn_list - list of functions f: Course -> bool
    """
    bools = [True] * len(courses)
    for i in xrange(len(courses)):
        for fn in fn_list:
            if not fn(courses[i]):
                # Deselect course, then proceed to process next course
                bools[i] = False
                break
    return bools

def duration_eq(n):
    """
    Returns a function that returns true if the Course's duration is exactly
    equal to n.
    """
    return lambda crs: crs.duration() == n

def duration_ge(n):
    """
    Returns a function that returns true if the Course's duration is greater
    than or equal to n.
    """
    return lambda crs: crs.duration() >= n

def duration_le(n):
    """
    Returns a function that returns true if the Course's duration is less
    than or equal to n.
    """
    return lambda crs: crs.duration() <= n

def islab():
    """Returns a function that returns true if the Course is a lab."""
    return lambda crs: crs.islab()

def isupperdiv():
    """Returns a function that returns true if the Course is an upper division course."""
    return lambda crs: crs.isupperdiv()

def occurs_after(time):
    """
    Returns a function that returns true if the Course starts at or after
    the given time (Time object).
    """
    return lambda crs: crs.occurs_after(time)

def occurs_before(time):
    """
    Returns a function that returns true if the Course ends at or before
    the given time (Time object).
    """
    return lambda crs: crs.occurs_before(time)

def starts_at(time):
    """
    Returns a function that returns true if the Course has a Lecture that
    starts at the specified time (Time object).
    """
    return lambda crs: crs.starts_at(time)

def ends_at(time):
    """
    Returns a function that returns true if the Course has a Lecture that
    ends at the specified time (Time object).
    """
    return lambda crs: crs.ends_at(time)
