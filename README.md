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

# Local Dev

## Requirements

* `make` (a classic)
* Docker configured in a way that networking and files work
* python 3.8
* no not believin' in yo self

## Frontend

```
$ REACT_ROOMBAHT_API_ENDPOINT="http://localhost:8000/" make frontend_dev
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

Use `make artifacts` to generate the frontend and backend artifacts.

There are two scripts to be used for modifying deployed hosts. They each take two arguments; a SSH username and remote host. Ask an adult for your SSH username and the remote host name.

* `./scripts/provision user 127.0.0.1` is to be run when a host is first created and when any baseline non-application changes are desired. It will execute `./scripts/provision-remote.sh` on the remote host.
* `./scripts/deploy user 127.0.0.1` is used to move the generated artifacts to the deployed host and perform the various steps needed for them to be active. This includes
  * python `virtualenv` management
  * `nginx` configuration
  * `systemd` for the django bits
* You can easily view frontend (nginx) and backend (django/wsgi) logs remotely
  * `./scripts/roombaht_ctl user 127.0.0.1 frontend-log`
  * `./scripts/roombaht_ctl user 127.0.0.1 backend-log`
* You can completely wipe the database as well. Helpful during pre-season development and a terrible idea once the gates have opened.
  * `./scripts/roombaht_ctl user 127.0.0.1 wipe`

# Data Population

*Note* This data population is meant to run only once after the initial DB migrations are applied. It has slightly different invocation for local dev and remote. This script will create the initial set of rooms and "staff" users. If the script detects that it has already been run on a database, it will ask for a confirmation. Because it does need to wipe the tables and start anew.

## Local

```
source backend/venv/bin/activate
source scripts/dev.env
python backend/createStaffAndRooms.py samples/exampleMainRoomList.csv samples/exampleMainStaffList.csv
```

## Remote

This script will handle secrets and moving files to the remote host for you. Remember to ask an adult for your username and a host name.

```
./scripts/roombaht_ctl user 127.0.0.1 init samples/exampleMainRoomList.csv samples/exampleMainStaffList.csv
```

# DB Schema

schemaV0.01

```
[Room]
|number|take3_name|hotel_name|available|guest|swap_code|swap_time|

[Guest]
|email|name|jwt|ticket|invite|room_number|

```
