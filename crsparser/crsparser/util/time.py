import re
import util

class TimeInterval(object):
    """A time interval, consisting of a start time and an end time."""
    
    def __init__(self, start, end, align = True):
        """
        Arguments:

        start - a Time object or string to be used to construct a Time object
                representing the start of the time interval
        end - a Time object or string representing the end of the time interval
        align - whether str(self) will return an aligned version of the interval,
                e.g. " 7:00- 8:00" will align vertically with "10:00-14:50"
        """
        if isinstance(start, Time) and isinstance(end, Time):
            self.start = start
            self.end = end
            self.align = align
        elif isinstance(start, str) and isinstance(end, str):
            self.start = Time(start)
            self.end = Time(end)
            self.align = align
        else:
            raise TypeError("Invalid types (must be a pair of strings or Times")

    def __str__(self):
        """
        Concatenates str(self.start), "-", and str(self.end). Note that if
        any Time's hours < 10, there will be a space before that time,
        unless self.align is set to False.
        """
        if self.align:
            return str(self.start) + "-" + str(self.end)
        else:
            return str(self.start).strip() + "-" + str(self.end).strip()

    def contains(self, time):
        """
        Returns whether this TimeInterval contains the given time (Time object).
        Accepts either a string or a Time object as an argument.
        """
        if isinstance(time, Time):
            if self.end >= self.start:
                return self.start <= time and self.end >= time
            else:
                return self.start <= time or self.end >= time
        else:
            if self.end >= self.start:
                return self.start <= Time(time) and self.end >= Time(time)
            else:
                return self.start <= Time(time) or self.end >= Time(time)

    def duration(self):
        """Returns the duration of the TimeInterval in minutes."""
        return self.end - self.start

class Time(object):
    """
    A specific time of day, as on a 24 hour clock. Can convert from am/pm to
    24-hour time. Does not keep track of seconds.
    """
    # Group 1 = hours, group 2 = minutes, group 3 = a, p, or None
    TIME_REGEX = r"([0-9]{1,2})\s*:\s*([0-9]{2})(?:\s*(a|A|p|P)|\b)"

    TIME_FSTR = "{0:>2d}:{1:02d}"
    MINS_PER_DAY = 1440

    def __init__(self, time):
        """
        Converts the string time to a 24-hour time. Does not check minutes
        for validity, so 5:74 is the same as 6:14. However, does convert all
        hours to a number between 0 and 23 and minutes to a number between
        0 and 59.
        
        time - a string representing the time, such as "7:00"; the format is
               "hh:mm" with an optional "a|am|p|pm"; 
        """
        r = re.match(Time.TIME_REGEX, time)
        if r is not None:
            hours = r.group(1)
            mins = r.group(2)
            pm = 0                  # Convert from pm to 24 hour time
            if r.group(3) != None and "p" in r.group(3).lower():
                pm = 1
                    
            if util.isint(hours) and util.isint(mins):       
                self.hours = int(hours) % 24 + int(mins) / 60 + 12 * pm
                self.mins = int(mins) % 60
            else:
                raise ValueError("Invalid time format")
        else:
            raise ValueError("Invalid time format")

    def __eq__(self, other):
        """Returns true if the two times are equal, and false otherwise."""
        if (self.hours * 60 + self.mins) == (other.hours * 60 + other.mins):
            return True
        else:
            return False

    def __ge__(self, other):
        """Returns true if self is after or the same time as other, and false otherwise."""
        if (self.hours * 60 + self.mins) >= (other.hours * 60 + other.mins):
            return True
        else:
            return False

    def __gt__(self, other):
        """Returns true if self is after other, and false otherwise."""
        if (self.hours * 60 + self.mins) > (other.hours * 60 + other.mins):
            return True
        else:
            return False
    
    def __le__(self, other):
        """Returns true if self is before or the same time as other, and false otherwise."""
        if (self.hours * 60 + self.mins) <= (other.hours * 60 + other.mins):
            return True
        else:
            return False
    
    def __lt__(self, other):
        """Returns true if self is before other, and false otherwise."""
        if (self.hours * 60 + self.mins) < (other.hours * 60 + other.mins):
            return True
        else:
            return False

    def __sub__(self, start):
        """
        Returns the difference self - start in minutes. Assumes that
        if start is after self on the clock, the duration passes midnight.
        """
        mins1 = self.hours * 60 + self.mins
        mins2 = start.hours * 60 + start.mins
        if mins1 >= mins2:
            return mins1 - mins2
        else:                       # Passing midnight
            return Time.MINS_PER_DAY - mins2 + mins1

    def __str__(self):
        """Returns the time hh:mm; the hours are padded with one space if h < 10."""
        return Time.TIME_FSTR.format(self.hours, self.mins)
