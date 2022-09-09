from datetime import datetime, timedelta
from typing import Set

import requests
import time

from hungry.Storage import Storage
from hungry.shift import Shift


class HungryAPI:
    """ A class for communicating with the Hungry Api.

    The HungryAPI class is responsible for handling the communication with the Hungry API.
    It uses the undocumented usehurrier.com API to authenticate and retrieve data.

    Args:
        email (str): The email to use for authentication
        password (str): The password to use for authentication
        employee_id (str): The employee id found in the Roadrunner app -> my profile -> id
    """
    TIMEZONE = "Europe/Copenhagen"
    # get latest app version URL
    APP_VERSION_DOMAIN: str = "https://api.appcenter.ms/v0.1/public/sdk/apps/91607026-b44d-46a9-86f9-7d59d86e3105/releases/latest"
    API_DOMAIN: str = "https://dk.usehurrier.com"
    URL_AUTH = f"{API_DOMAIN}/api/mobile/auth"
    # The time that in seconds after which the token is considered expired
    TOKEN_EXPIRY_SECONDS: int = 3500  # 100 sec buffer
    # default fallback app version
    app_version: int = 291
    app_short_version: str = "v3.2209.4"

    def __init__(self, email: str, password: str, employee_id: int):
        self.EMAIL: str = email
        self.PASSWORD: str = password
        self.EMPLOYEE_ID: int = employee_id

        # URLS
        self.URL_SWAPS: str = f"{HungryAPI.API_DOMAIN}/api/rooster/v3/employees/{employee_id}/available_swaps"
        self.URL_UNASSIGNED: str = f"{HungryAPI.API_DOMAIN}/api/rooster/v3/employees/{employee_id}/available_unassigned_shifts"
        self.URL_TAKE_SWAP: str = f"{HungryAPI.API_DOMAIN}/api/rooster/v3/{{}}/swap"
        self.URL_TAKE_UNASSIGNED: str = f"{HungryAPI.API_DOMAIN}/api/rooster/v3/unassigned_shifts/{{}}/assign"

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
            resp = requests.post(HungryAPI.URL_AUTH, headers=headers, json=data)
            resp.raise_for_status()
            resp_json = resp.json()
            Storage().token = resp_json["token"]
            Storage().token_expiration = time.time() + HungryAPI.TOKEN_EXPIRY_SECONDS
            Storage().city_id = resp_json["city_id"]
        except Exception:
            raise Exception("Failed to authenticate! Wrong credentials?")

    @staticmethod
    def _get_app_version() -> (int, str):
        """ Returns a tuple of (app_version, app_short_version).

        For example:
            (291, "v3.2209.4")
        In case of failure, fallback values are returned.

        Returns:
            int, str: app version and short app version
        """

        # fallback version
        version = 291
        short_version = "v3.2209.4"

        resp = requests.get(HungryAPI.APP_VERSION_DOMAIN)
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

    def refresh_token(decorated):
        """ A decorator for refreshing the token if it is expired. """
        def wrapper(api, *args, **kwargs):
            storage = Storage()
            if storage.token_expiration is None or time.time() > storage.token_expiration:
                api.authenticate()
            return decorated(api, *args, **kwargs)

        return wrapper

    @refresh_token
    def _get_swap_shifts(self):
        resp = requests.get(self.URL_SWAPS, params=self.__get_params(), auth=BearerAuth(Storage().token))
        resp.raise_for_status()
        return resp.json()

    @refresh_token
    def _get_unassigned_shifts(self):
        resp = requests.get(self.URL_UNASSIGNED, params=self.__get_params(), auth=BearerAuth(Storage().token))
        resp.raise_for_status()
        return resp.json()

    def get_shifts(self) -> Set[Shift]:
        swap_shifts: set = HungryAPI._resp_to_shifts(self._get_swap_shifts())
        unassigned_shifts: set = HungryAPI._resp_to_shifts(self._get_unassigned_shifts())
        found_shifts: set = swap_shifts.union(unassigned_shifts)

        return found_shifts

    # function to automatically take a shift
    def take_shift(self, shift: Shift):
        """ Takes a shift, automatically.

        Args:
            shift (Shift): shift to take

        """
        if shift.status == "PENDING":
            self._take_swap_shift(shift)
        elif shift.status == "UNASSIGNED":
            self._take_unassigned_shift(shift)
        else:
            raise Exception("Shift is not pending or unassigned.Shift status is " + shift.status)

    def _take_swap_shift(self, shift: Shift):
        url_take_swap = self.URL_TAKE_SWAP.format(shift.id)
        resp = requests.post(url_take_swap, auth=BearerAuth(self.token))
        resp.raise_for_status()

    def _take_unassigned_shift(self, shift: Shift):
        url_take_unassigned = self.URL_TAKE_UNASSIGNED.format(shift.id)
        body = {
            "id": shift.id,
            "start_at": shift.start_at,
            "end_at": shift.end_at,
            "starting_point_id": shift.starting_point_id,
            "employee_ids": [self.EMPLOYEE_ID]
        }
        resp = requests.post(url_take_unassigned, auth=BearerAuth(self.token), json=body)
        resp.raise_for_status()
    def __get_params(self) -> dict:
        """ Returns a dictionary of parameters for the GET request for getting shifts. """
        return {"start_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "end_at": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "city_id": Storage().city_id,
                "with_time_zone": HungryAPI.TIMEZONE
                }

    @staticmethod
    def _resp_to_shifts(shifts: list) -> Set[Shift]:
        """ Converts a list of dictionary represented shifts to a set of Shift objects.

        Args:
            shifts: response from the server as json

        Returns:
            Set[Shift]: set of shifts
        """
        shift_objects = set()
        for shift in shifts:
            shift_id = shift["id"]
            start = datetime.strptime(shift["start"], "%Y-%m-%dT%H:%M:%S")
            end = datetime.strptime(shift["end"], "%Y-%m-%dT%H:%M:%S")
            status = shift["state"]
            time_zone = shift["time_zone"]
            starting_point_id = shift["starting_point_id"]
            starting_point_name = shift["starting_point_name"]
            shift = Shift(shift_id, start, end, status, time_zone, starting_point_id, starting_point_name)
            shift_objects.add(shift)
        return shift_objects


class BearerAuth(requests.auth.AuthBase):
    """ A wrapper around requests auth class for using Bearer token to communication with the Hungry API.

    Returns:
        requests.auth.AuthBase: the auth class
    """
    def __init__(self, token: str):
        self.token: str = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r
