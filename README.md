
# Getting Started
Install the deps and `python manage.py runserver`
Run the `populate_reservations.py` script to add new Rooms or Guests. Currently this naiively jams the csvs into the db
to remove all Rooms and Guests run `Room.objects.all().delete()` in interpreter. Brute force af. 

## Django and React
Django is good at managing relations and providing an api for controlling models. React is good at consuming stuffs and making things look good while they flossing. 

### Django
Python framework to provide the api model of rooms and guests.


Proposed DB schemaV0.01

```
[Room]
|number|take3_name|hotel_name|available|guest|swap_code|swap_time

[Guest]
|email|name|jwt|ticket|invite|room_number|

```


### React
install deps
```
npm install
npm install axios bootstrap reactstrap react-bs-datatable--save
```

## Dev setup

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

Run it:
```
python manage.py runserver 0.0.0.0:8000
and then another terminal:
cd frontend && npm start
```

### Dependencies
You will need a .env file with a bunch of env vars. details to come. or you know, figure it out
