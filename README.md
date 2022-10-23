# RS RoomBot Application!
It sweeps, it mops. It swaps rooms for a few hundred guests at conference style events.
Facilitates participants trading accomodations and answering the critical question of, "where the party at".

![alt text](samples/roombot.png?raw=true)

# Getting Started
Install the deps and `python manage.py runserver && npm start`
Run the `populate_reservations.py` script to add new Rooms or Guests. 

## Django and React
Django is good at managing relations and providing an api for controlling models. React is good at consuming stuffs and making things look good while they flossing. 


## Dev setup
All the usual python env bits and npm things

### Django
Python framework to provide the api model of rooms and guests.

schemaV0.01

```
[Room]
|number|take3_name|hotel_name|available|guest|swap_code|swap_time|

[Guest]
|email|name|jwt|ticket|invite|room_number|

```

First time:
```
python manage.py makemigrations --empty --name reservations reservations
```

Then the usual make migrations migrate.

Model changes:
```
python manage.py makemigrations
python manage.py migrate
```

Source the env vars:
```
source backend/.env
```

### React
All the usual frontend stuff.
install deps

```
npm install
npm install axios font-awesome bootstrap reactstrap react-bs-datatable --save
```


### Run it
```
cd backend && python manage.py runserver 0.0.0.0:8000
```
in another terminal
```
cd frontend && npm start
```

### Dependencies
You will need a .env file with a bunch of env vars. Main spreadsheets are not checked in. 
