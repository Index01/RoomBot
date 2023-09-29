# RS RoomBot Application!
It sweeps, it mops. It swaps rooms for a few hundred guests at conference style events.
Facilitates participants trading accomodations and answering the critical question of, "where the party at".

![alt text](samples/roombot.png?raw=true)

# Built With

* Django is good at managing relations and providing an api for controlling models. Used for the Room and Guest API model.
* React is good at consuming stuffs and making things look good while they flossing.

# Local Dev

## Requirements

* `make` (a classic)
* Docker configured in a way that networking and files work
* python3.8

## Frontend

```
$ make frontend_dev
$ make frontend_build
```

This should build a docker image, use it to generate the react static, and then start react in dev mode listening on port 3000.

## Backend

```
$ export SECRET_KEY="narrative"
$ export EMAIL_HOST_PASSWORD="words"
$ make backend_dev
```

This should ensure proper depdendencies, initialize and run migrations on sqlite, and start the backend running on port 8080.

## Population

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
