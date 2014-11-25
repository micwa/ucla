"""
Miscellaneous utility functions that do error checking, conversion, etc.
"""

def isint(n):
    """Returns true if n can be casted to an int."""
    try:
        int(n)
        return True
    except ValueError:
        return False

def stoi(s):
    """Converts a string to an int by ignoring all nondigit characters."""
    s = "".join([c for c in s if c.isdigit()])
    return int(s)