# from functools import singledispatch
from datetime import datetime, time
from typing import List
from datetime import timedelta


class RecurringTimeslot():
    '''
    A recurring timeslot. If a shift falls within the timeslot, it is considered to be valid shift.

    Attributes:
        start_time (time): The start time of the timeslot.
        end_time (time): The end time of the timeslot.
        days (List[Day]): The days of the week the timeslot occurs on (starting with Monday=0).
        minMinutes (int): The minimum number of minutes a shift must be, to be considered valid.
    '''
    def __init__(self, recurring_days: List[int], start: time, end: time, min_minutes: int):
        self.start = start
        self.end = end
        self.min_minutes = min_minutes
        self.recurring_days = recurring_days


    '''
    Returns the name of the day from the day number supplied as int starting with monday = 0
    or none if not a valid day.
    '''
    @staticmethod
    def _get_day_name(day_number: int):
        if day_number < 0 or day_number > 6:
            return None
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_number]

    '''
    Returns the day number from the day name supplied as string starting with monday = 0
    or none if not a valid day.
    '''
    @staticmethod
    def _day_name_to_int(day_name):
        return {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }[day_name.strip().lower()]

    '''
    Returns True if a shift falls within the timeslot, False otherwise.
    
    Args:
        start (time): The start time of the shift.
        end (time): The end time of the shift.
        
    Returns:
        bool: True if the shift falls within the timeslot, False otherwise.
    '''

    def is_valid_shift(self, start: datetime, end: datetime):
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

    '''
    Returns a string representation of the timeslot in the format of:
    "10:00-12:00 every Monday, Wednesday, Friday where minimum shift length is 30 minutes"
    '''
    def __str__(self):
        return "{}-{} every {} where minimum shift length is {} minutes".format(
            self.start.strftime("%H:%M"),
            self.end.strftime("%H:%M"),
            ", ".join([self._get_day_name(day) for day in self.recurring_days]),
            self.min_minutes
        )

    def __repr__(self):
        return self.__str__()

    '''
    Serialize
    '''
    def serialize(self):
        return {
            "start": self.start.strftime("%H:%M"),
            "end": self.end.strftime("%H:%M"),
            "days": self.recurring_days,
            "min_minutes": self.min_minutes
        }

    '''
    Deserialize
    '''
    @staticmethod
    def deserialize(json_data):
        return RecurringTimeslot(
            json_data["days"],
            datetime.strptime(json_data["start"], "%H:%M").time(),
            datetime.strptime(json_data["end"], "%H:%M").time(),
            json_data["min_minutes"]
        )