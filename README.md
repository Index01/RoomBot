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
$ make frontend_dev
```

This should build a docker image, use it to generate the react static, and then start react in dev mode listening on port 3000.

## Backend

```
$ export SECRET_KEY="narrative"
$ export EMAIL_HOST_PASSWORD="words"
$ make backend_dev
```

This should ensure proper depdendencies, initialize and run migrations on sqlite, and start the backend running on port 8080.

# Managing a Real Host

Use `make artifacts` to generate the frontend and backend artifacts.

There are two scripts to be used for modifying deployed hosts. They each take two arguments; a SSH username and remote host.

* `./scripts/provision user 127.0.0.1` is to be run when a host is first created and when any baseline non-application changes are desired. It will execute `./scripts/provision-remote.sh` on the remote host.
* `./scripts/deploy user 127.0.0.1` is used to move the generated artifacts to the deployed host and perform the various steps needed for them to be active. This includes
  * python `virtualenv` management
  * `nginx` configuration
  * `systemd` for the django bits

# Data Population

*Note* Be careful doing this as there are global-vars-as-config.

Run the `populate_reservations.py` script to add new Rooms or Guests.

# DB Schema

schemaV0.01

```
[Room]
|number|take3_name|hotel_name|available|guest|swap_code|swap_time|

[Guest]
|email|name|jwt|ticket|invite|room_number|

```
