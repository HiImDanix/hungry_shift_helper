import argparse
import apprise
import requests
import time

API_DOMAIN: str = "https://dk.usehurrier.com"
URL_AUTH = f"{API_DOMAIN}/api/mobile/auth"
TOKEN_EXPIRY_SECONDS: int = 3500  # 100 sec buffer


class Hungry:
    TIMEZONE = "Europe/Copenhagen"
    APP_VERSION: int = 291
    APP_SHORT_VERSION: str = "v3.2209.4"

    def __init__(self, email: str, password: str, employee_id: int):
        self.EMAIL: str = email
        self.PASSWORD: str = password
        self.EMPLOYEE_ID: int = employee_id

        self.shift_ids = set()

        # URLS
        self.URL_SWAPS: str = f"{API_DOMAIN}/api/rooster/v3/employees/{employee_id}/available_swaps"
        self.URL_UNASSIGNED: str = f"{API_DOMAIN}/api/rooster/v3/employees/{employee_id}/available_unassigned_shifts"

        # App version
        self.APP_VERSION: int
        self.APP_SHORT_VERSION: str
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

    @staticmethod
    def _get_app_version() -> (int, str):
        # https://api.appcenter.ms/v0.1/public/sdk/apps/91607026-b44d-46a9-86f9-7d59d86e3105/releases/latest
        return 291, "v3.2209.4"

    def refresh_token(decorated):
        def wrapper(api, *args, **kwargs):
            if time.time() > api.token_expiration:
                api.authenticate()
            return decorated(api, *args, **kwargs)

        return wrapper

    @refresh_token
    def _get_swap_shifts(self):
        resp = requests.get(self.URL_SWAPS, params=params, auth=BearerAuth(self.token)).json()
        return [{'shift_id': 77151, 'start': '2022-03-17T16:00:00', 'end': '2022-03-17T20:00:00', 'status': 'PENDING', 'time_zone': 'Europe/Copenhagen', 'starting_point_id': 3, 'starting_point_name': 'Aalborg bike'}]
        return resp

    @refresh_token
    def _get_unassigned_shifts(self):
        resp = requests.get(self.URL_UNASSIGNED, params=params, auth=BearerAuth(self.token)).json()
        return resp

    def get_shifts(self):
        swap_shifts: dict = self._get_swap_shifts()
        unassigned_shifts: dict = self._get_unassigned_shifts()
        found_shifts: dict = swap_shifts + unassigned_shifts
        found_shift_ids: set = set(shift["shift_id"] for shift in found_shifts)
        new_shift_ids: set = found_shift_ids - self.shift_ids
        self.shift_ids = found_shift_ids

        new_shifts = []
        for shift in found_shifts:
            if shift["shift_id"] in new_shift_ids:
                new_shifts.append(shift)
        return new_shifts


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
    hungry = Hungry(args.email, args.password, args.id)

    print("Running!")
    run_continuously: bool = (args.frequency is not None)
    while run_continuously:
        params = {"start_at": "2022-03-08T21:52:24.847Z",
                  "end_at": "2030-03-30T05:59:59.999Z",
                  "city_id": hungry.city_id,
                  "with_time_zone": hungry.TIMEZONE
                  }

        shifts = hungry.get_shifts()

        if len(shifts) != 0:
            print("Found a shift!!")
            appriseObj.notify(body=str(shifts), title='Hungry has found some shifts!!!')
            print(shifts)
        time.sleep(args.frequency)
