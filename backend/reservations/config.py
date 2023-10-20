import os

DEV = os.environ.get('ROOMBAHT_DEV', 'FALSE').lower() == 'true'
DEV_MAIL = os.environ.get('ROOMBAHT_DEV_MAIL', '')
SEND_MAIL = os.environ.get('ROOMBAHT_SEND_MAIL', 'FALSE').lower() == 'true'
LOGLEVEL = os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper()

URL_HOST = os.environ.get('ROOMBAHT_HOST', 'localhost')
URL_PORT = os.environ.get('ROOMBAHT_PORT', '80')
URL_SCHEMA = os.environ.get('ROOMBAHT_SCHEMA', 'http')

JWT_KEY = os.environ['ROOMBAHT_JWT_KEY']

SEND_ONBOARDING = os.environ.get('ROOMBAHT_SEND_ONBOARDING', 'false').lower() == 'true'

TEMP_DIR = os.environ.get('ROOMBAHT_TMP', '/tmp')