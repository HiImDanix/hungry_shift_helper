
![Logo](https://u.cubeupload.com/mrdanix448/Asset26x.png)


# Hungry Shift Helper [![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/) ![Abandoned](https://img.shields.io/badge/status-abandoned-red.svg)

a CLI app that automatically notifies you on Discord, Slack, Telegram etc. when there's a shift available for https://hungry.dk riders. \
Just specify your timeslots, and leave it running 24/7.




## Why?

On February 27th, Hungry decided to make changes for riders working for them with an international student contract. They decided that from the day onwards, you have to call them every Monday 09:00-18:00 to secure the shifts for the next week.\
\
On top of that, they considerably reduced the amount of shifts available for taking.\
\
One day, I forgot to call. I needed those hours. However, I knew that every now and then a fellow rider wants to swap a shift. To take use of this, you have to monitor their app 24/7.\
\
And so - 'I can make a script for that', I thought.
## Features

- Specify your preferred timeslots
- Get notified when a shift is available on 70+ services with [Apprise](https://github.com/caronc/apprise/wiki)
- Leave running 24/7
- Automatically take shifts [experimental]

## Installation

Clone the repository

```bash
https://github.com/HiImDanix/hungry_shift_helper.git && cd hungry_shift_helper/
```
    
Install dependencies
```
pip install -r requirements.txt
```

## Get started

Set up your preferred timeslots for when you want to work
```
python timeslot_creator.py
```

Run the main script with *email, password, employeeID, appriseURL* as the arguments
```
python run.py email@email.com password 11111 discord://webhook_id/webhook_token
```

Make it run 24/7, every 30 seconds
```
python run.py email@email.com password 11111 discord://webhook_id/webhook_token -f 30
```
Recommendation: Use cron on Linux and Task Scheduler on Windows instead of using the the -f / --frequency argument, to not have to leave the script running.
## Available arguments

**Required**
Argument | Description
--- | ---
1.`email`  | Your hungry.dk email.
2.`password`  | Your hungry.dk password.
3.`id`  | Your hungry.dk employee ID (see app -> my profile).
4.`notify`  | An [Apprise notification URL](https://github.com/caronc/apprise/wiki).

**Optional**

Short | Long | Description
--- | ---  | ---
`-h`  | `--help` | Shows a help message and exits.
 \- | `--auto-take` | Automatically takes shifts (that fit your chosen timeslots).
`-f <seconds>`  | `--frequency <seconds>` | Executes the script continuously every <seconds>.
`-d`  | `--debug` | Enables debug mode.

## Screenshots

![Timeslot screenshot](https://i.imgur.com/Y5jZWd1.png)

![Help screenshot](https://i.imgur.com/6ixhftU.png)

![Notification screenshot](https://i.imgur.com/jprRQL9.png)

