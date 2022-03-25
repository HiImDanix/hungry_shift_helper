import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Set
from functools import singledispatch

import apprise
import requests
import time

from shift import Shift
from timeslot import RecurringTimeslot

API_DOMAIN: str = "https://dk.usehurrier.com"
URL_AUTH = f"{API_DOMAIN}/api/mobile/auth"
# The time that in seconds after which the token is considered expired
TOKEN_EXPIRY_SECONDS: int = 3500  # 100 sec buffer
# get latest app version URL
APP_VERSION_DOMAIN: str = "https://api.appcenter.ms/v0.1/public/sdk/apps/91607026-b44d-46a9-86f9-7d59d86e3105/releases/latest"


class HungryAPI:
    TIMEZONE = "Europe/Copenhagen"
    # default fallback app version
    app_version: int = 291
    app_short_version: str = "v3.2209.4"

    ''''
    The HungryAPI class is responsible for handling the communication with the Hungry API.
    It uses the undocumented usehurrier API to authenticate and retrieve data.
    Notifications are handled by Apprise.
    
    Args:
        username (str): The username to use for authentication
        password (str): The password to use for authentication
        employee_id (str): The employee id found in the Roadrunner app -> my profile -> id
    '''
    def __init__(self, email: str, password: str, employee_id: int):
        self.EMAIL: str = email
        self.PASSWORD: str = password
        self.EMPLOYEE_ID: int = employee_id

        self.previously_found_shifts = set()

        # URLS
        self.URL_SWAPS: str = f"{API_DOMAIN}/api/rooster/v3/employees/{employee_id}/available_swaps"
        self.URL_UNASSIGNED: str = f"{API_DOMAIN}/api/rooster/v3/employees/{employee_id}/available_unassigned_shifts"

        # App version
        self.app_version: int
        self.app_short_version: str
        self.APP_VERSION, self.APP_SHORT_VERSION = self._get_app_version()

        # Authenticate
        self.authenticate()

    def authenticate(self):
        print("Authenticating!")
        data = {"user": {"user_name": self.EMAIL, "password": self.PASSWORD}}
        headers = {"user-agent": f"Roadrunner/ANDROID/{self.APP_VERSION}/{self.APP_SHORT_VERSION}"}
        try:
            resp = requests.post(URL_AUTH, headers=headers, json=data)
            resp.raise_for_status()
        except Exception as e:
            raise Exception("Failed to authenticate! Wrong credentials?")
        else:
            self.token_expiration = time.time() + TOKEN_EXPIRY_SECONDS

        try:
            resp_json = resp.json()

            self.token: str = resp_json["token"]
            self.contract_type: str = resp_json["contract_type"].lower()
            self.city_id: int = resp_json["city_id"]
            self.city_name: str = resp_json["city_name"].lower()
        except Exception as e:
            raise Exception("Server responded with unexpected data while trying to authenticate")

    '''
    Returns the app version and short app version
    For example:
        (291, "v3.2209.4")
    
    Returns:
        int, str: app version and short app version
    '''
    @staticmethod
    def _get_app_version() -> (int, str):
        # fallback version
        version = 291
        short_version = "v3.2209.4"

        resp = requests.get(APP_VERSION_DOMAIN)
        # if response is not ok, return default values
        if not resp.ok:
            return version, short_version

        # parse response
        resp_json = resp.json()

        # fallback version
        if "version" not in resp_json and "short_version" not in resp_json:
            return version, short_version

        # return version and short version
        return int(resp_json["version"]), resp_json["short_version"]

    '''
    A decorator for refreshing the token if it is expired
    '''
    def refresh_token(decorated):
        def wrapper(api, *args, **kwargs):
            if time.time() > api.token_expiration:
                api.authenticate()
            return decorated(api, *args, **kwargs)

        return wrapper

    @refresh_token
    def _get_swap_shifts(self):
        resp = requests.get(self.URL_SWAPS, params=HungryAPI._get_params(), auth=BearerAuth(self.token))
        resp.raise_for_status()
        return resp.json()

    @refresh_token
    def _get_unassigned_shifts(self):
        resp = requests.get(self.URL_UNASSIGNED, params=HungryAPI._get_params(), auth=BearerAuth(self.token))
        resp.raise_for_status()
        return resp.json()

    def get_shifts(self) -> Set[Shift]:

        swap_shifts: set = HungryAPI._resp_to_shifts(self._get_swap_shifts())
        unassigned_shifts: set = HungryAPI._resp_to_shifts(self._get_unassigned_shifts())
        found_shifts: set = swap_shifts.union(unassigned_shifts)

        new_shifts: Set[Shift] = found_shifts - self.previously_found_shifts
        self.previously_found_shifts = found_shifts

        return new_shifts

    '''
    Returns parameters for the requests that
    '''
    @staticmethod
    def _get_params() -> dict:
        return {"start_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                  "end_at": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                  "city_id": hungry.city_id,
                  "with_time_zone": hungry.TIMEZONE
                  }

    '''
    Converts a response from the server to a set of shift objects
    
    :param resp: response from the server as json
    :return: set of shifts
    '''
    @staticmethod
    def _resp_to_shifts(shifts: list) -> Set[Shift]:
        shift_objects = set()
        for shift in shifts:
            id = shift["shift_id"]
            start = datetime.strptime(shift["start"], "%Y-%m-%dT%H:%M:%S")
            end = datetime.strptime(shift["end"], "%Y-%m-%dT%H:%M:%S")
            status = shift["status"]
            time_zone = shift["time_zone"]
            starting_point_id = shift["starting_point_id"]
            starting_point_name = shift["starting_point_name"]
            shift = Shift(id, start, end, status, time_zone, starting_point_id, starting_point_name)
            shift_objects.add(shift)
        return shift_objects

'''
A wrapper around requests auth class that allows to use Bearer token for communication with the Hungry API
'''#
class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token: str):
        self.token: str = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Checks if there are shifts available on hungry.dk',
                                     epilog='Good luck in your shift search! :)')
    parser.add_argument("email", help="Your hungry.dk email", type=str)
    parser.add_argument("password", help="Your hungry.dk password", type=str)
    parser.add_argument("id", help="Your hungry.dk employee ID (see app -> my profile)", type=int)
    parser.add_argument("notify", help="Apprise notification URL")
    parser.add_argument("-f", "--frequency", help="Executes the script every <seconds> (use CRON instead!)",
                        metavar="seconds", type=int)
    args = parser.parse_args()

    # Notifications
    appriseObj = apprise.Apprise()
    if appriseObj.add(args.notify) is False:
        raise Exception("The given Apprise notification URL is invalid. ")

    # Hungry
    hungry = HungryAPI(args.email, args.password, args.id)

    # Create a recurring timeslot that covers all days of week, all hours, and all shift lengths
    # days of week
    days_of_week = [0, 1, 2, 3, 4, 5, 6]
    # start and end time
    start = datetime.strptime("00:00", "%H:%M")
    end = datetime.strptime("23:59", "%H:%M")
    # min shift length (minutes)
    shift_length = 0
    # create a recurring timeslot
    timeslot = RecurringTimeslot(days_of_week, start.time(), end.time(), shift_length)

    # Run once or every args.frequency seconds
    print("Starting the script...")
    while True:
        # Get shifts
        shifts = hungry.get_shifts()
        # get timeslots
        timeslots = [timeslot]

        # Get shifts that satisfy the user specified timeslots
        valid_shifts = [shift for shift in shifts if timeslot.is_valid_shift(shift.start, shift.end)]

        # Notify if a valid shift is found
        if len(shifts) > 0:
            print(f"Found {len(shifts)} new shifts!")
            for shift in valid_shifts:
                shifts_repr: str = '\n'.join(str(s) for s in shifts)
                print(shifts_repr)
                appriseObj.notify(body=shifts_repr, title=f"{len(shifts)} new shifts found!")
        if args.frequency is None:
            break
        time.sleep(args.frequency)
    print("Done!")
