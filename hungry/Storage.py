import json
import os

from hungry.shift import Shift
from hungry.timeslot import RecurringTimeslot


class Singleton(type):
    """ Singleton metaclass """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Storage(metaclass=Singleton):
    """ Allows to store and retrieve data from files

    It can load and save timeslots, shifts, and token with its expiration datetime

    """

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

    def add_recurring_timeslot(self, timeslot):
        self._recurring_timeslots.append(timeslot)
        self.save_recurring_timeslots(self._recurring_timeslots)

    def delete_recurring_timeslot(self, timeslot):
        self._recurring_timeslots.remove(timeslot)
        self.save_recurring_timeslots(self._recurring_timeslots)

    def add_shift(self, shift):
        self._shifts.append(shift)
        self.save_shifts(self._shifts)

    # Load data to memory
    def _load_to_cache(self):
        self._recurring_timeslots = self._load_recurring_timeslots()
        self._shifts = self._load_shifts()
        self._token, self._token_expiration, self._city_id = self._load_token_and_cityid()

    # Save data to files
    def _save_cache_to_files(self):
        self.save_timeslots(self._timeslots)
        self.save_shifts(self._shifts)
        self.save_token(self._token, self._token_expiration, self.city_id)

    def get_recurring_timeslots(self):
        if len(self._recurring_timeslots) == 0:
            self._load_recurring_timeslots()
        return self._recurring_timeslots

    def get_shifts(self):
        """ Return cached shifts or load from file """
        if len(self._shifts) == 0:
            self._load_shifts()
        return self._shifts

    def get_token_and_cityid(self):
        """ Return a tuple of (cached token, expiration, city id) from cache or files """
        if self._token is None:
            self._load_token_and_cityid()
        return self._token, self._token_expiration, self._city_id

    def save_token_and_cityid(self, token: str, expires: float, city_id: int):
        """ Save token, expiration datetime, and city id to files & cache"""
        with open(self.directory + 'token.json', 'w') as f:
            json.dump({'token': token, 'expires': expires, 'city_id': city_id}, f)
        self._token = token
        self._token_expiration = expires
        self._city_id = city_id

    def save_recurring_timeslots(self, timeslots):
        """ Save recurring timeslots to json file and memory cache. """
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

    def _load_recurring_timeslots(self):
        """ Return a list of recurring timeslots from files, or empty list if file doesn't exist or is corrupted. """
        try:
            with open(self.directory + 'recurring_timeslots.json', 'r') as f:
                try:
                    return [RecurringTimeslot.deserialize(ts) for ts in json.load(f)]
                except json.decoder.JSONDecodeError:
                    return []
        except FileNotFoundError:
            return []

    def _load_shifts(self):
        """ Return a list of shifts from files, or empty list if file doesn't exist or is corrupted. """
        try:
            with open(self.directory + 'shifts.json', 'r') as f:
                try:
                    return [Shift.deserialize(s) for s in json.load(f)]
                except json.decoder.JSONDecodeError:
                    return []
        except FileNotFoundError:
            return []

    def _load_token_and_cityid(self):
        """ Return a a tuple (token, expiry, city_id) from files, or empty tuple if file is corrupted/doesn't exist.

        Returns:
            (str, float, int) -- (token, expiry, city_id)
        """

        try:
            with open(self.directory + 'token.json', 'r') as f:
                try:
                    token_data = json.load(f)
                    return token_data['token'], token_data['expires'], token_data['city_id']
                except json.decoder.JSONDecodeError:
                    return None, None, None
        except FileNotFoundError:
            return None, None, None
