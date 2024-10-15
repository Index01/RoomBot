import os
from importlib import resources as impresources
import reservations


DEV = os.environ.get('ROOMBAHT_DEV', 'FALSE').lower() == 'true'
DEV_MAIL = os.environ.get('ROOMBAHT_DEV_MAIL', '')
SEND_MAIL = os.environ.get('ROOMBAHT_SEND_MAIL', 'FALSE').lower() == 'true'
LOGLEVEL = os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper()

URL_HOST = os.environ.get('ROOMBAHT_HOST', 'localhost')
URL_PORT = os.environ.get('ROOMBAHT_PORT', '80')
URL_SCHEMA = os.environ.get('ROOMBAHT_SCHEMA', 'http')

JWT_KEY = os.environ['ROOMBAHT_JWT_KEY']

TEMP_DIR = os.environ.get('ROOMBAHT_TMP', '/tmp')

GUEST_HOTELS = os.environ.get('ROOMBAHT_GUEST_HOTELS', 'Ballys,Nugget').split(',')

VERSION = impresources.read_text(reservations, "version")

ROOM_COOLDOWN = int(os.environ.get('ROOMBAHT_ROOM_COOLDOWN', 900))
