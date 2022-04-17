import json
import os

from hungry.shift import Shift
from hungry.timeslot import RecurringTimeslot


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Storage(metaclass=Singleton):
    '''
    This class allows loading and saving of data to and from a file database.
    It can load and save timeslots, shifts, and token with expiration datetime.
    '''
    def __init__(self, directory='data/'):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.directory = base_dir = directory

        # If the directory doesn't exist, create it
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        # Cache
        self._recurring_timeslots = []
        self._shifts = []
        self._token = None
        self._token_expiration = None
        self._city_id = None

        # Load from files to cache
        self._load_to_cache()

    @property
    def city_id(self):
        return self.get_token_and_cityid()[2]

    @property
    def recurring_timeslots(self):
        return self.get_recurring_timeslots()

    @property
    def shifts(self):
        return self.get_shifts()

    @property
    def token(self):
        return self.get_token_and_cityid()[0]

    @property
    def token_expiration(self):
        return self.get_token_and_cityid()[1]

    # Add recurring timeslot
    def add_recurring_timeslot(self, timeslot):
        self._recurring_timeslots.append(timeslot)
        self.save_recurring_timeslots(self._recurring_timeslots)

    # Delete recurring timeslot
    def delete_recurring_timeslot(self, timeslot):
        self._recurring_timeslots.remove(timeslot)
        self.save_recurring_timeslots(self._recurring_timeslots)

    # Add shift
    def add_shift(self, shift):
        self._shifts.append(shift)
        self.save_shifts(self._shifts)

    def _load_to_cache(self):
        self._recurring_timeslots = self._load_recurring_timeslots()
        self._shifts = self._load_shifts()
        self._token, self._token_expiration, self._city_id = self._load_token_and_cityid()

    def _save_cache_to_files(self):
        self.save_timeslots(self._timeslots)
        self.save_shifts(self._shifts)
        self.save_token(self._token, self._token_expiration, self.city_id)

    def get_recurring_timeslots(self):
        if len(self._recurring_timeslots) == 0:
            self._load_recurring_timeslots()
        return self._recurring_timeslots

    # Return cached shifts or load from file
    def get_shifts(self):
        if len(self._shifts) == 0:
            self._load_shifts()
        return self._shifts

    # Return cached token, expiration and city id or load from file
    def get_token_and_cityid(self):
        if self._token is None:
            self._load_token_and_cityid()
        return self._token, self._token_expiration, self._city_id



    ''' 
    Save token, expiration datetime, and city id to json file and memory cache.
    '''
    def save_token_and_cityid(self, token: str, expires: float, city_id: int):
        with open(self.directory + 'token.json', 'w') as f:
            json.dump({'token': token, 'expires': expires, 'city_id': city_id}, f)
        self._token = token
        self._token_expiration = expires
        self._city_id = city_id

    '''
    Save recurring timeslots to json file and memory cache.
    '''
    def save_recurring_timeslots(self, timeslots):
        with open(self.directory + 'recurring_timeslots.json', 'w') as f:
            json.dump([ts.serialize() for ts in timeslots], f)
        self._recurring_timeslots = timeslots

    '''
    Save shifts to json file and memory cache.
    '''
    def save_shifts(self, shifts):
        with open(self.directory + 'shifts.json', 'w') as f:
            json.dump([s.serialize() for s in shifts], f)
        self._shifts = shifts

    '''
    Load recurring timeslots from json file
    '''
    def _load_recurring_timeslots(self):
        # deserialize json and load from file if exists
        try:
            with open(self.directory + 'recurring_timeslots.json', 'r') as f:
                try:
                    return [RecurringTimeslot.deserialize(ts) for ts in json.load(f)]
                except json.decoder.JSONDecodeError:
                    return []
        except FileNotFoundError:
            return []

    '''
    Load shifts from json file
    '''
    def _load_shifts(self):
        try:
            with open(self.directory + 'shifts.json', 'r') as f:
                try:
                    return [Shift.deserialize(s) for s in json.load(f)]
                except json.decoder.JSONDecodeError:
                    return []
        except FileNotFoundError:
            return []

    '''
    Load token from json file along with expiration datetime.

    Returns:
        token: str
        expires: datetime
        city_id: int
    '''
    def _load_token_and_cityid(self):
        try:
            with open(self.directory + 'token.json', 'r') as f:
                try:
                    json_file = json.load(f)
                    return json_file['token'], json_file['expires'], json_file['city_id']
                except json.decoder.JSONDecodeError:
                    return None, None, None
        except FileNotFoundError:
            return None, None, None
