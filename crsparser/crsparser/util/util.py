"""
Miscellaneous utility functions for error-checking and conversion.
"""

def isint(n):
    """Returns true if n can be casted to an int."""
    try:
        int(n)
        return True
    except ValueError:
        return False

def stoi(s):
    """
    Converts a string to an int by ignoring all nondigit characters and all
    characters after periods (truncates floats).
    """
    s2 = ""
    for c in s:
        if c.isdigit():
            s2 += c
        elif c == ".":
            break

    if s2 == "":
        raise ValueError("Not a number convertible to an int")
        
    return int(s2)
