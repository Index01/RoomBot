import logging
import os
import random
import sys

from datetime import datetime
from csv import DictReader, DictWriter
from django.core.mail import EmailMessage, get_connection
import reservations.config as roombaht_config

logging.basicConfig(stream=sys.stdout,
                    level=roombaht_config.LOGLEVEL)

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
    # filter out comments and blank lines
    input_dict = DictReader(filter(lambda row: len(row) > 0 and row[0]!='#', csv_iter), skipinitialspace=True)
    input_fields = [k.lstrip().rstrip() for k in input_dict.fieldnames if type(k)==str]
    for elem in input_dict:
        strip_elem = {k.lstrip().rstrip(): v.lstrip().rstrip() for k, v in elem.items() if type(k)==str and type(v)==str}
        input_items.append(strip_elem)

    return input_fields, input_items

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

def my_url():
    port = roombaht_config.URL_PORT
    if port not in ("80", "443"):
        port = ":%s" % port

    return "%s://%s%s" % (
        roombaht_config.URL_SCHEMA,
        roombaht_config.URL_HOST,
        port
    )

def ts_suffix():
    now = datetime.now()
    return "%s-%s-%s-%s-%s" % (now.day, now.month, now.year, now.hour, now.minute)

def send_email(addresses, subject, body, attachments=[]):
    if not roombaht_config.SEND_MAIL:
        logger.info("Would have sent email to %s, subject: %s", ','.join(addresses), subject)
        return

    real_addresses = []
    for address in addresses:
        if not roombaht_config.DEV:
            # normal production email sending
            real_addresses.append(address)
        else:
            # development mode is a bit more special
            if '@noop.com' not in address:
                # always send to normal emails
                real_addresses.append(address)
            else:
                if roombaht_config.DEV_MAIL != '':
                    # if the ROOMBAHT_DEV_MAIL var is set then insert the address part
                    #   of the @noop.com email address as a suffix and treat as normal
                    email_address, _email_host = address.split('@')
                    dev_address, dev_host = roombaht_config.DEV_MAIL.split('@')
                    real_addresses.append(f"{dev_address}+{email_address}@{dev_host}")
                else:
                    # otherwise just pretend to send the email
                    logger.debug("Would have sent email to %s, subject: %s", address, subject)
                    return

    msg = EmailMessage(subject=subject,
                       body=body,
                       to=real_addresses,
                       connection = get_connection())

    for attachment in attachments:
        if os.path.exists(attachment):
            msg.attach_file(attachment)
        else:
            logger.warning("attachment %s not found sending email to %s",
                           attachment, ','.join(addresses))

    logger.info("Sending email to %s, subject: %s", ','.join(real_addresses), subject)

    msg.send()
