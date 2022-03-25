from datetime import datetime


class Shift():
    def __init__(self, id: int, start: datetime, end: datetime, status: str,
                 time_zone: str, starting_point_id: int, starting_point_name: str):
        self.id = id
        self.start = start
        self.end = end
        self.status = status
        self.time_zone = time_zone
        self.starting_point_id = starting_point_id
        self.starting_point_name = starting_point_name

    # Override equals
    def __eq__(self, other):
        if isinstance(other, Shift):
            return self.id == other.id
        return False

    '''
    A string representation of the Shift object in the format of:
    "February 4, 14:00-16:00 (2h 30 minutes)"
    note: It assumes that start end happen on the same day
    '''
    def __str__(self):
        return "{} {} from {} ({}h {}m)".format(
            self.start.strftime("%B"),
            self.start.day,
            self.start.strftime("%H:%M") + "-" + self.end.strftime("%H:%M"),
            (self.end - self.start).seconds // 3600,
            ((self.end - self.start).seconds // 60) % 60
        )

    '''
    A string representation of the Shift object in the format of:
    "February 4, 14:00-16:00 (2h 30 minutes)"
    note: It assumes that start end happen on the same day
    '''
    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.id)