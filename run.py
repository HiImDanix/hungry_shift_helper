import argparse
from datetime import datetime
from typing import List, Set

import apprise
import time

from hungry.hungryAPI import HungryAPI
from hungry.shift import Shift
from hungry.timeslot import RecurringTimeslot
from hungry.Storage import Storage
import logging


def main():
    parser = argparse.ArgumentParser(description='Checks if there are shifts available on hungry.dk',
                                     epilog='Good luck in your shift search! :)')
    parser.add_argument("email", help="Your hungry.dk email", type=str)
    parser.add_argument("password", help="Your hungry.dk password", type=str)
    parser.add_argument("id", help="Your hungry.dk employee ID (see app -> my profile)", type=int)
    parser.add_argument("notify", help="Apprise notification URL")
    parser.add_argument("--auto-take", help="Automatically take shifts (that fit your chosen timeslots)",
                        action="store_true",
                        default=False)
    parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")
    parser.add_argument("-f", "--frequency", help="Executes the script every <seconds>",
                        metavar="seconds", type=int)
    args = parser.parse_args()

    # set up logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.info("Starting the script")

    # Notifications
    appriseObj: apprise.Apprise = apprise.Apprise()
    if appriseObj.add(args.notify) is False:
        logging.info("Failed to parse apprise notification URL. Exiting...")
        raise Exception("The given Apprise notification URL is invalid. ")

    # Hungry API
    hungry: HungryAPI = HungryAPI(args.email, args.password, args.id)

    # Storage for timeslots, previously found shifts, login token
    storage: Storage = Storage()

    # if no recurring timeslots are present, and take shifts is enabled -> confirm action
    if args.auto_take and len(storage.recurringTimeslots) == 0:
        print("No recurring timeslots are set and auto-take is enabled. Do you want to continue? [y/n]")
        if input().lower() != "y":
            exit(0)

    # Load timeslots from storage
    if len(storage.recurring_timeslots) == 0:
        logging.info("No timeslots found. Creating a default one that covers everything")
        # timeslot that covers all days and times
        timeslot: RecurringTimeslot = get_eternal_timeslot()
        storage.recurring_timeslots = [timeslot]

    # Run once or every args.frequency seconds
    logging.debug("Starting the main part of the script")
    while True:
        try:
            # Get shifts from API
            shifts: Set[Shift] = hungry.get_shifts()
            logging.debug(f"Got {len(shifts)} shifts from API")
            # show the shifts in debug
            for shift in shifts:
                logging.debug(f"Shift: {shift}")

            # Get previously found shifts
            saved_shifts: List[Shift] = storage.shifts
            logging.debug(f"Got {len(saved_shifts)} shifts from storage")

            # Identify unique shifts
            new_shifts: List[Shift] = [shift for shift in shifts if shift not in saved_shifts]
            logging.debug(f"Found {len(new_shifts)} unique shifts")

            # Save all retrieved shifts
            storage.shifts = shifts

            # Get shifts that satisfy the user specified timeslots
            valid_shifts: Set = set()
            for timeslot in storage.recurring_timeslots:
                for shift in new_shifts:
                    if timeslot.is_valid_shift(shift.start, shift.end):
                        valid_shifts.add(shift)
            logging.debug(f"Retrieved timeslots: {storage.recurring_timeslots}")
            logging.debug(f"Identified {len(valid_shifts)} valid shifts")

            # Automatically take shifts, if enabled
            if args.auto_take:
                for shift in valid_shifts:
                    logging.info(f"Taking shift {shift}")

                    # Take the shift
                    hungry.take_shift(shift)
                    logging.debug(f"Shift taken")

            # Notify user if a valid shift(s) is found
            if len(valid_shifts) > 0:
                title: str = f"{len(valid_shifts)} new shifts were " + ('procured.' if args.auto_take else 'found.')
                body: str = '\n'.join(str(s) for s in valid_shifts)
                appriseObj.notify(body=body, title=title)
            else:
                logging.info("No shifts found")
            if args.frequency is None:
                break
            logging.info("Script finished")

        except Exception as e:
            logging.error(f"Error: {e}")
            try:
                appriseObj.notify(body=str(e), title="Hungry-Shift-Helper error")
            except Exception as e:
                logging.error(f"Could not send error message: {e}")
        # sleep
        if args.frequency:
            time.sleep(args.frequency)
        else:
            break


def get_eternal_timeslot() -> RecurringTimeslot:
    """ Returns a RecurringTimeslot object that covers all dates and times"""
    # days of week
    days_of_week: List = [0, 1, 2, 3, 4, 5, 6]
    # start and end time
    start: datetime = datetime.strptime("00:00", "%H:%M")
    end: datetime = datetime.strptime("23:59", "%H:%M")
    # min shift length (minutes)
    shift_length: int = 0
    # return a recurring timeslot
    return RecurringTimeslot(days_of_week, start.time(), end.time(), shift_length)

if __name__ == "__main__":
    main()



