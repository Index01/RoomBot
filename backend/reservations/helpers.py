import logging
import os
import random
import sys

from datetime import datetime
from csv import DictReader, DictWriter
from django.core.mail import EmailMessage, get_connection

logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

logger = logging.getLogger('Helpers')

def egest_csv(items, fields, filename):
    with open(filename, 'w') as output_handle:
        output_dict = DictWriter(output_handle, fieldnames=fields)
        output_dict.writeheader()
        for elem in items:
            output_dict.writerow(elem)

def ingest_csv(filename):
    # turns out DictReader will accept any iterable object
    csv_iter = None
    if isinstance(filename, str):
        if not os.path.exists(filename):
            raise Exception("input file %s not found" % filename)
        csv_iter = open(filename, "r")
    elif isinstance(filename, list):
        csv_iter = filename
    else:
        raise Exception('must pass filename or list to ingest_csv')

    input_dict = []
    input_items = []
    input_dict = DictReader(csv_iter, skipinitialspace=True)
    input_fields = [k.lstrip().rstrip() for k in input_dict.fieldnames if type(k)==str]
    for elem in input_dict:
        strip_elem = {k.lstrip().rstrip(): v.lstrip().rstrip() for k, v in elem.items() if type(k)==str and type(v)==str}
        input_items.append(strip_elem)

    return input_fields, input_items

def is_dev():
    return os.environ.get('ROOMBAHT_DEV', 'FALSE').lower() == 'true'

def phrasing():
    words = None
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open("%s/../config/wordylyst.md" % dir_path , "r") as f:
        words = f.read().splitlines()
    word = words[random.randint(0, 999)].capitalize()+words[random.randint(0, 999)].capitalize()
    rand = random.randint(1,3)
    if(rand==1):
        word = word+str(random.randint(0,99))
    elif(rand==2):
        word = word+str(random.randint(0,99))+words[random.randint(0,999)].capitalize()
    else:
        word = word+words[random.randint(0,999)].capitalize()
    return word

def hostname():
    host = os.environ['ROOMBAHT_HOST']
    port = os.environ.get('ROOMBAHT_PORT', 80)
    schema = os.environ.get('ROOMBAHT_SCHEMA', 'http')

    if port not in (80, 443):
        port = ":%s" % port

    return "%s://%s%s" % (schema, host, port)

def ts_suffix():
    now = datetime.now()
    return "%s-%s-%s-%s-%s" % (now.day, now.month, now.year, now.hour, now.minute)
