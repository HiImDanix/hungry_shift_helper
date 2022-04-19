# from functools import singledispatch
from datetime import datetime, time
from typing import List
from datetime import timedelta


class RecurringTimeslot():
    """ A recurring timeslot that repeats every week on specified days and at specified times.

    Attributes:
        recurring_days (List[str]): The days of the week on which the timeslot occurs (0-6).
        start (time): The time at which the timeslot starts.
        end (time): The time at which the timeslot ends.
        min_minutes (int): The minimum number of minutes a shift must be to fit in this timeslot.
    """

    def __init__(self, recurring_days: List[int], start: time, end: time, min_minutes: int):
        self.start: time = start
        self.end: time = end
        self.min_minutes: int = min_minutes
        self.recurring_days: List[int] = recurring_days

    @staticmethod
    def _get_day_name(day_number: int):
        """ Returns the name of the weekday from number (0-6). """
        if day_number < 0 or day_number > 6:
            return None
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_number]

    @staticmethod
    def _day_name_to_int(day_name):
        """ Returns a day's number from its full name (e.g. Monday = 0), or None. Case insensitive. """
        return {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }[day_name.strip().lower()]

    def is_valid_shift(self, start: datetime, end: datetime):
        """ Returns True if a shift falls within the timeslot, False otherwise.

        Args:
            start (time): The start time of the shift.
            end (time): The end time of the shift.
        """

        # Correct day
        if start.weekday() not in self.recurring_days:
            return False

        # Start and end time falls within timeslot
        if start.time() < self.start or end.time() > self.end:
            return False

        # (end-start) satisfies the minimum amount of minutes requirement
        if (end - start).seconds / 60 < self.min_minutes:
            return False
        return True

    def __str__(self):
        """ Returns a string representation of the timeslot.

        The representation returned is in the format:
        10:00-12:00 every Monday, Wednesday, Friday where minimum shift length is 30 minutes

        """
        return "{}-{} every {} where minimum shift length is {} minutes".format(
            self.start.strftime("%H:%M"),
            self.end.strftime("%H:%M"),
            ", ".join([self._get_day_name(day) for day in self.recurring_days]),
            self.min_minutes
        )

    def __repr__(self):
        return self.__str__()

    def serialize(self):
        """ Returns a dictionary representation of the timeslot. """
        return {
            "start": self.start.strftime("%H:%M"),
            "end": self.end.strftime("%H:%M"),
            "days": self.recurring_days,
            "min_minutes": self.min_minutes
        }

    @staticmethod
    def deserialize(json_data):
        """ Returns a RecurringTimeslot object from a dictionary representation. """
        return RecurringTimeslot(
            json_data["days"],
            datetime.strptime(json_data["start"], "%H:%M").time(),
            datetime.strptime(json_data["end"], "%H:%M").time(),
            json_data["min_minutes"]
        )