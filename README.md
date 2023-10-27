# RS RoomBot Application!

It sweeps, it mops. It swaps rooms for a few hundred guests at conference style events.
Facilitates participants trading accomodations and answering the critical question of, "where the party at".

![alt text](samples/roombot.png?raw=true)

# Built With

* Django is good at managing relations and providing an api for controlling models. Used for the Room and Guest API model.
* React is good at consuming stuffs and making things look good while they flossing.

# Environment / Configuration

Configuration is handled through environment variables, which are stored encrypted in GitHub. Secret management is handled through the `./scripts/secrets` script. You must have a file named `.secret` in the top level of the Git repository. Contact an adult for the contents of this file.

* `./scripts/decrypt` generate the `secrets.env` file from encrypted source
* `./scripts/encrypt` encrypt the `secrets.env` file
* `./scripts/show` display all the env vars in a format suitable for `eval`
* `./scripts show VAR` display the contents of the desired env var, stripped of quotes

## Settings

* `ROOMBAHT_DEV` Should be set to `true` on dev and never on prod. Controls DB usage and enables some local dev functionality. Defaults to `false`.
* `ROOMBAHT_DEV_MAIL` if this is set to an email address then any address for the `@noop.com` domain will be converted to be a prefix email. Example `foo@gmail.com` and `bar@noop.com` would convert to `foo+bar@gmail.com`. Helpful for testing room swaps. Defaults to disabled.
* `ROOMBAHT_SEND_MAIL` Needs to be set to `true` for email to be sent. Defaults to `false`.
* `ROOMBAHT_SEND_ONBOARDING` Needs to be set to `true` for the onboarding emails to be sent during Secret Party export ingestion. Defaults to `false`.
* `ROOMBAHT_LOGLEVEL` Controls the Python log level. Should be set to one of `ERROR`, `WARNING`, `INFO`, `DEBUG`. Defaults to `INFO` on prod and `DEBUG` on dev.
* `ROOMBAHT_HOST` is the hostname part of the url to be used when generating our url in emails and wherever else. Defaults to `localhost`.
* `ROOMBAHT_PORT` is the port part of the url to be used when generating our url in emails and wherever else. Defaults to `80`.
* `ROOMBAHT_SCHEMA` is the schema part of the url. Defaults to `http`.
* `ROOMBAHT_TMP` is where we yeet temporary files. Defaults to `/tmp`.
* `ROOMBAHT_IGNORE_TRANSACTIONS` This is a CSV list of transactionts to not care about.
* `ROOMBAHT_JWT_KEY` is basically the salt for o ur auth tokens. This must be set, there is no default.
* `ROOMBAHT_DJANGO_SECRET_KEY` Might not even be used since we don't use Django sessions?
* `ROOMBAHT_DB_PASSWORD` This is the postgres password for production. This must be set, there is no default.
* `ROOMBAHT_DB_HOST` This is the postgres hostname for production. This must be set, there is no default.
* `ROOMBAHT_EMAIL_HOST_USER` This is the SMTP user and it must be set, there is no default.
* `ROOMBAHT_EMAIL_HOST_PASSWORD` This is the SMTP password and it must be set, there is no default.

# Local Dev

## Requirements

* `make` (a classic)
* Docker configured in a way that networking and files work
* python 3.8 w/`virtualenv`
* A variety of "system packages" (note package names may vary on non-Linux)
  * `build-essential`
  * `imagemagik`
  * `libpq-dev`
  * `python3-dev`
* no not believin' in yo self

## Frontend

```
$ DEV=true make frontend_dev
```

This should build a docker image, use it to generate the react static, and then start react in dev mode listening on port 3000.

## Backend

To run the backend in dev mode, you will need something like the following env vars:
```sh
export ROOMBAHT_DEV="true"
export ROOMBAHT_DJANGO_SECRET_KEY="narrative"
export ROOMBAHT_EMAIL_HOST_PASSWORD="words"
export ROOMBAHT_EMAIL_HOST_USER="words"
export ROOMBAHT_SEND_MAIL="true"
```
You can run `source dev.env` to export the example values stored in that file.

To run the local dev django server, call
```sh
make backend_dev
```

This should ensure proper depdendencies, initialize and run migrations on sqlite, and start the backend running on port 8080.


# Managing a Real Host

Use `make archive` to generate the frontend and backend artifacts. By default this will build the frontend pointing at the production frontend host. To point at a different environment, specify the `API_ENV` variable.

```
$ API_ENV=dev make archive
$ API_ENV=staging make archive
```

There are two scripts to be used for modifying deployed hosts. They each take two arguments; a SSH username and remote host. Ask an adult for your SSH username and the remote host name.

* `./scripts/provision user 127.0.0.1` is to be run when a host is first created and when any baseline non-application changes are desired. It will execute `./scripts/provision-remote.sh` on the remote host.
* `./scripts/deploy user 127.0.0.1 <env>` is used to move the generated artifacts to the deployed host and perform the various steps needed for them to be active. You must specify the `prod` or `staging` environment. Make sure you are pointing the right environment at the right host! This includes
  * python `virtualenv` management
  * `nginx` configuration
  * `systemd` for the django bits
* Run `init` to load the Rooms and Staff tables, generally after a `wipe` and/or `deploy`
  * `./scripts/roombaht_ctl user 127.0.0.1 init ${ROOM_FILE} ${STAFF_FILE}`
* You can easily view frontend (nginx) and backend (django/wsgi) logs remotely
  * `./scripts/roombaht_ctl user 127.0.0.1 frontend-log`
  * `./scripts/roombaht_ctl user 127.0.0.1 backend-log`
* You can completely wipe the database as well. Helpful during pre-season development and a terrible idea once the gates have opened. After a helful confirmation prompt, this will wipe the database and re-run the migrations.
  * `./scripts/roombaht_ctl user 127.0.0.1 wipe`
* You can directly invoke a the django management tool, which gives you access to a variety of administrative tools.
  * `./scripts/roombaht_ctl user 127.0.0.1 manage shell` - invoke the djangok shell will full access to the orm and every module in the project

# Data Population

*Note* This data population is meant to run only once after the initial DB migrations are applied. It has slightly different invocation for local dev and remote. This script will create the initial set of rooms and "staff" users. If the script detects that it has already been run on a database, it will ask for a confirmation. Because it does need to wipe the tables and start anew.

## Local

```
source backend/venv/bin/activate
source dev.env
python backend/createStaffAndRooms.py samples/exampleMainRoomList.csv samples/exampleMainStaffList.csv
```

To get a guest password, you can go to the Django management console.
First, already have a running backend.
Then, run `python backend/manage.py shell`
And in the python terminal, enter
```python
from reservations.models import Guest
Guest.objects.filter(email="mpesaven@gmail.com")[0].jwt
```

## Remote

This script will handle secrets and moving files to the remote host for you. Remember to ask an adult for your username and a host name.

```
./scripts/roombaht_ctl user 127.0.0.1 init samples/exampleMainRoomList.csv samples/exampleMainStaffList.csv
```

## Images

Images are kinda like data? There is a script that will either work based on an existing downloaded folder (i.e. if you have GDrive setup on a computer) or will attempt to use `gdown` to fetch the folder magially. It will then generate thumbnails and put the images in the right place. Not these images will _not_ end up in the git repo.

```
./scripts/fetch-images
./scripts/fetch-images /path/to/gdrive/images
```

## Data Sanitization

There is a script which will take live data from the room list spreadsheet and a Secret Party export and appropriately anonymize it. For the room list, some randomness may be applied, and there are configurable weights. All guests and placers listed in the room list will be sourced from the original room list.

For the guest list, the following changes are made

* The first and last name are changed
* The email is changed
  * Duplicate emails (per name) are mapped down to a single email
* Transfer to / from is mapped to the appropriate names
* Phone number is randomly generated per name

For the room list, the following changes are made

* The first and last name are changed.
  * Secondary names, if present, are also changed
* Placers (art and manual room) are selected from a randomly generated group.
* All blank `Placed By` fields are replaced with `Roombaht`
* Optionally, placed rooms may be randomly generated, ignoring original selections (weight name `placed`, default 10%).
* Optionally, secondary names may be randomly added to placed rooms (weight name `secondary`, default 50%).
* Art room types are always selected from a randomly generated group.
* Optionally, a random selection of rooms will become art rooms (weight name `art`, default 5%).
* Optionally, placed rooms have a chance to be set as changable (weight name `changeable`, default 50%)

```
python ./backend/scripts/massage_csv.py /tmp/SecretPartyExport.csv /tmp/RoomsSheetExport.csv --weight placed:30,art:10
```

# DB Schema

## Guest

Tracks every guest. Every guest the system is aware of will have a room associated.

* `name` The full name of a registered guest.
* `email` The email of a guest. Ued for login.
* `ticket` The Secret Party ticket ID.
* `invitation` The Secret Party invitation ID.
* `jwt` The (per user) magical token of hope and wonder and access.
* `room_number` The room a guest is located in.

## Staff

Staff can do staff like things.

* `name` The short name / alias for the staff.
* `email` The email address for the staff.
* `is_admin` A boolean that may or may not be set to true.
* `guest` A mapping to a guest record.

## Room

Rooms are where the party is.

* `number` The room number.
* `name_take3` The internal name for the room. What a user will see.
* `name_hotel` The hotel room name.
* `is_available` Whether or not the room is in any way available.
* `is_swappable` Whether or not the room is swappable. Must also be available.
* `is_smoking` Is it a smoking room? Maps from room features.
* `is_lakeview` Is it a lake view room? Maps from room features.
* `is_ada` Is it an accessible room? Maps from room features.
* `is_hearing_accessible` Is the room hearing accessible i.e. does it have visual indicators for alarm conditions. Maps from room features.
* `swap_code` The code used for swapping a room.
* `swap_time` The date and time of when the room was swapped.
* `check_in` The check in date.
* `check_out` The check out date.
* `notes` General notes about the room.
* `guest_notes` Rooms specific to the guest in the room.
* `sp_ticket_id` The Secret Party ticket ID.
* `primary` The full name of the primary resident in the room.
* `secondary` The full name of a secondary person in the room.
* `placed_by_roombot` Indicates that this is a room which can be placed by roombot. Implies not a placed room.
* `guest` A mapping to a guest record.
