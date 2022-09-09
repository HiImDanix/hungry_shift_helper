import json

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
    """ A class to store data, persistently."""
    def __init__(self, filename='data.json'):
        self.filename = filename

        # data
        self._recurring_timeslots = []
        self._shifts = []
        self._token = None
        self._token_expiration = None
        self._city_id = None

        # Load data to memory
        self._load_data_to_memory()

    def _load_data_to_memory(self):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                self._recurring_timeslots = [RecurringTimeslot.deserialize(ts) for ts in data['recurring_timeslots']]
                self._shifts = [Shift.deserialize(s) for s in data['shifts']]
                self._token = data['token']
                self._token_expiration = data['token_expiration']
                self._city_id = data['city_id']
        except FileNotFoundError:
            pass

    def _save_data_to_file(self):
        with open(self.filename, 'w') as f:
            json.dump({
                'recurring_timeslots': [ts.serialize() for ts in self._recurring_timeslots],
                'shifts': [s.serialize() for s in self._shifts],
                'token': self._token,
                'token_expiration': self._token_expiration,
                'city_id': self._city_id
            }, f)

    # *** Properties & setters (auto-save to file) ***
    @property
    def city_id(self):
        return self._city_id

    @city_id.setter
    def city_id(self, city_id):
        self._city_id = city_id
        self._save_data_to_file()

    @property
    def recurring_timeslots(self):
        return self._recurring_timeslots

    @recurring_timeslots.setter
    def recurring_timeslots(self, timeslots):
        self._recurring_timeslots = timeslots
        self._save_data_to_file()

    @property
    def shifts(self):
        return self._shifts

    @shifts.setter
    def shifts(self, shifts):
        self._shifts = shifts
        self._save_data_to_file()

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._token = token
        self._save_data_to_file()

    @property
    def token_expiration(self):
        return self._token_expiration

    @token_expiration.setter
    def token_expiration(self, token_expiration):
        self._token_expiration = token_expiration
        self._save_data_to_file()
