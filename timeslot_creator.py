from hungry.timeslot import RecurringTimeslot
from hungry.Storage import Storage
from datetime import datetime

# Add new timeslot
def create_timeslot(storage):

    # Allow user to input days of the week such as Monday, Tuesday, etc.
    days_of_the_week = input("Enter days of the week separated by commas: ")
    # Use Timeslot.day_name_to_int for each day to convert the user input to a list of integers
    days_of_the_week = [RecurringTimeslot._day_name_to_int(day) for day in days_of_the_week.split(',')]

    # Allow user to input start and end times
    try:
        start_time = input("Enter start time: ")
        start_time = datetime.strptime(start_time, '%H:%M')
        end_time = input("Enter end time: ")
        end_time = datetime.strptime(end_time, '%H:%M')
    except ValueError:
        print("Invalid time format. Please use HH:MM")
        exit()

    # Get minimum shift length duration:
    try:
        min_shift_length = int(input("Enter minimum shift length in minutes: "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        exit()
    if min_shift_length < 0:
        raise ValueError("Min duration must be greater than 0")

    # If minimum shift length is greater than the difference between start and end times, raise error
    if (end_time - start_time).seconds < min_shift_length * 60:
        raise ValueError("Min duration must be less than the difference between start and end times")

    # Create a new recurring timeslot
    return RecurringTimeslot(days_of_the_week, start_time.time(), end_time.time(), min_shift_length)


if __name__ == '__main__':
    storage = Storage()

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
            user_input = int(input("\nEnter option: "))
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
                timeslot_number = int(input("Enter timeslot to delete: "))

                # try to get timeslot object
                try:
                    timeslot = storage.recurring_timeslots[timeslot_number - 1]
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




