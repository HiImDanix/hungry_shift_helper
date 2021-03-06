from hungry.timeslot import RecurringTimeslot
from hungry.Storage import Storage
from datetime import datetime


def main():
    """ Allows the user to specify preferred recurring timeslots. """

    storage: Storage = Storage()

    while True:
        print("-" * 80)
        print("\nCurrent timeslots:")
        for i, timeslot in enumerate(storage.recurring_timeslots):
            print(f"{i + 1}. {timeslot}")
        print("\nOptions:")
        print("1. Add new timeslot")
        print("2. Delete a timeslot by its number")
        print("3. Exit")

        # Get user input
        try:
            user_input: int = int(input("\nEnter option: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        # Add new timeslot
        if user_input == 1:
            try:
                storage.add_recurring_timeslot(create_timeslot(storage))
            except ValueError as e:
                print(e)
                continue
            print("Timeslot added successfully")
        # Delete a timeslot by its number
        elif user_input == 2:
            try:
                # Get timeslot number
                timeslot_number: int = int(input("Enter timeslot to delete: "))

                # try to get timeslot object
                try:
                    timeslot: RecurringTimeslot = storage.recurring_timeslots[timeslot_number - 1]
                except IndexError:
                    print("Invalid timeslot number")
                    continue
                # Delete timeslot
                storage.delete_recurring_timeslot(timeslot)
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            print("Timeslot deleted successfully")
        # Exit
        elif user_input == 3:
            break
        else:
            print("Invalid input. Please choose an option from the list.")
            continue
    print("Exiting...")
    exit()


def create_timeslot():
    """ Asks the user for details to create a RecurringTimeslot object.

    Returns:
        RecurringTimeslot: The RecurringTimeslot object created.
    """

    success = False
    while not success:
        try:
            # Allow user to input days of the week such as Monday, Tuesday, etc.
            days_of_the_week = input("Enter days of the week separated by commas (Monday, Wednesday...): ")
            # Use Timeslot.day_name_to_int for each day to convert the user input to a list of integers
            days_of_the_week = [RecurringTimeslot._day_name_to_int(day) for day in days_of_the_week.split(',')]
            success = True
        except KeyError:
            print("Invalid day of the week. Please enter full day names e.g.: Monday, Wednesday, Friday")
            continue
        except KeyboardInterrupt:
            return

    success = False
    while not success:
        # Allow user to input start and end times
        try:
            start_time = input("Enter start time (23:59): ")
            start_time = datetime.strptime(start_time, '%H:%M')
            end_time = input("Enter end time (23:59): ")
            end_time = datetime.strptime(end_time, '%H:%M')
            success = True
        except ValueError:
            print("Invalid time format. Please use HH:MM\n")
            continue
        except KeyboardInterrupt:
            return

    success = False
    while not success:
        # Get minimum shift length duration:
        try:
            min_shift_length = int(input("Enter minimum shift length in minutes: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
        if min_shift_length < 0:
            print("Invalid input. Please enter a positive number.")
            continue
        # If minimum shift length is greater than the difference between start and end times
        if (end_time - start_time).seconds < min_shift_length * 60:
            print("Min duration must be less than the difference between start and end times")
            continue
        success = True

    # Create a new recurring timeslot
    return RecurringTimeslot(days_of_the_week, start_time.time(), end_time.time(), min_shift_length)


if __name__ == '__main__':
    main()
