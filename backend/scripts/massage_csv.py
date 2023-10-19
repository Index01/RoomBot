#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import termios
import tty

from datetime import datetime
from random import randint
from names_generator import generate_name
from lorem_text import lorem

from csv import DictReader, DictWriter

# don't judge
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from reservations.helpers import phrasing

logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

logger = logging.getLogger('MassageCSV')

def getch():
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    return _getch()

def parse_weights(weights_str):
    weights = {}
    if not weights_str:
        return weights

    for weight_str in weights_str.split(','):
        weight_bits = weight_str.split('=')
        weights[weight_bits[0]] = int(weight_bits[1])

    return weights

def random_placer(guest_names):
    placers = []
    for _num in range(randint(3, 8)):
        placers.append(guest_names[randint(0, len(guest_names) - 1)])

    def placer():
        return placers[randint(0, len(placers) - 1)]

    return placer

def art_room_types():
    art_types = []
    for _num in range(randint(2, 5)):
        art_types.append(phrasing())

    def art_type():
        return art_types[randint(0, len(art_types) - 1)]

    return art_type

def massage_rooms(input_items, guests, weights):
    output_items = []

    guest_names = []
    for guest in guests:
        a_name = "%s %s" % (guest['first_name'], guest['last_name'])
        if a_name not in guest_names:
            guest_names.append(a_name)

    get_placer = random_placer(guest_names)
    art_type = art_room_types()

    for item in input_items:
        new_name_bits = guest_names[randint(0, len(guest_names) - 1)].split(' ')
        new_first_name = new_name_bits[0]
        new_last_name = new_name_bits[1]

        new_item = {
            'Placement Verified': item['Placement Verified'],
            'Floor': item['Floor'],
            'Room': item['Room'],
            'Room Type': item['Room Type'],
            'Room Features (Accesbility, Lakeview, Smoking)(not visible externally)': item['Room Features (Accesbility, Lakeview, Smoking)(not visible externally)'],
            'Connected To Room': item['Connected To Room'],
            'Room Owned By (Secret Party)': item['Room Owned By (Secret Party)'],
            'Check-in Date': item['Check-in Date'],
            'Check-out Date': item['Check-out Date'],
            'Changeable': item['Changeable'],
            'Change Reason': item['Change Reason'],
            'Guest Restriction Notes': item['Guest Restriction Notes'],
            'Placement Team Notes': item['Placement Team Notes'],
            'Paying guest?': item['Paying guest?'],
            'Department': item['Department'],
            'Ticket ID in SecretParty': item['Ticket ID in SecretParty']
        }

        if randint(1, 100) <= weights.get('placed', 10):
            new_item['Placed By'] = get_placer()
            new_item['First Name (Resident)'] = new_first_name
            new_item['Last Name (Resident)'] = new_last_name
            if randint(1,100) <= weights.get('secondary', 50):
                new_item['Secondary Name'] = guest_names[randint(0, len(guest_names) - 1)]
        else:
            new_item['Placed By'] = 'Roombaht'


        if randint(1, 100) <= weights.get('art', 5):
            new_item['Art Room'] = 'Yes'
            new_item['Art Name / Placed Name'] = phrasing()
            new_item['Art Room Type'] = art_type()
        else:
            new_item['Art Room'] = 'No'

        output_items.append(new_item)

    return output_items

def massage_guests(input_items):
    output_items = []
    name_maps = {}
    email_maps = {}

    for item in input_items:
        a_name = "%s %s" % (item['first_name'], item['last_name'])
        new_name = generate_name(style = 'capital')
        new_name_bits = new_name.split(' ')
        new_first_name = new_name_bits[0]
        new_last_name = new_name_bits[1]
        new_email = "%s.%s@noop.com" % (new_first_name.lower(), new_last_name.lower())

        if a_name not in name_maps:
            name_maps[a_name] = "%s %s" % (new_first_name, new_last_name)

        if new_email not in email_maps:
            email_maps[item['email']] = new_email


    # actually anonymize
    for item in input_items:
        a_name = "%s %s" % (item['first_name'], item['last_name'])
        new_first_name, new_last_name = name_maps[a_name].split(' ')
        new_item = {
            'invitation_code': item['invitation_code'],
            'ticket_code': item['ticket_code'],
            'last_name': new_last_name,
            'first_name': new_first_name,
            'email': new_email,
            'phone': "", #anon
            'type': item['type'],
            'product': item['product'],
            'purchase_date': item['purchase_date'],
            'ticket_status': item['ticket_status']
        }

        if item['transferred_from'] != '':
            new_item['transferred_from'] = name_maps[a_name]
            new_item['transferred_from_email'] = email_maps[item['email']]
            new_item['transferred_from_code'] = item['transferred_from_code']

        if item['transferred_to'] != '':
            new_item['transferred_to'] = name_maps[a_name]
            new_item['transferred_to_email'] = email_maps[item['email']]

        output_items.append(new_item)

    return output_items

def ingest(filename):
    if not os.path.exists(filename):
        raise Exception("input file %s not found" % filename)

    input_dict = []
    input_items = []
    with open(filename, "r") as input_handle:
        input_dict = DictReader(input_handle, skipinitialspace=True)
        input_fields = [k.lstrip().rstrip() for k in input_dict.fieldnames if type(k)==str]
        for elem in input_dict:
            strip_elem = {k.lstrip().rstrip(): v.lstrip().rstrip() for k, v in elem.items() if type(k)==str and type(v)==str}
            input_items.append(strip_elem)

    return input_fields, input_items

def egest(items, fields, filename):
    with open(filename, 'w') as output_handle:
        output_dict = DictWriter(output_handle, fieldnames=fields)
        output_dict.writeheader()
        for elem in items:
            output_dict.writerow(elem)

def check_dest(filename, force):
    if os.path.exists(filename):
        if not force:
            print("Output file %s exists, overwrite? [y/n]" % filename)
            if getch().lower() != "y":
                raise Exception('user said no')
        else:
            print("Overwriting %s at user request" % filename)

def main(args):
    src_guest_list = args['guest_list']
    src_room_list = args['room_list']

    now = datetime.now()
    ts_suffix = "%s-%s-%s-%s-%s" % (now.day, now.month, now.year, now.hour, now.minute)

    dest_guest_list = "%s/guests-%s.csv" % (args['dest'], ts_suffix)
    dest_room_list = "%s/rooms-%s.csv" % (args['dest'], ts_suffix)

    check_dest(dest_guest_list, args['force'])
    check_dest(dest_room_list, args['force'])

    weights = parse_weights(args['weights'])

    guest_fields, original_guests = ingest(src_guest_list)
    room_fields, original_rooms = ingest(src_room_list)

    anon_guests = massage_guests(original_guests)
    anon_rooms = massage_rooms(original_rooms, anon_guests, weights)

    egest(anon_guests, guest_fields, dest_guest_list)
    egest(anon_rooms, room_fields, dest_room_list)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=('at least it has builtin help'),
                                     description='generate test data from real data')
    parser.add_argument('guest_list',
                        help='Path to guest list CSV file')
    parser.add_argument('room_list',
                        help='Path to room list CSV file')
    parser.add_argument('--dest',
                        help="Optional destination directory. Defaults to %s" % os.getcwd(),
                        default=os.getcwd())
    parser.add_argument('--force',
                        help='Force various destructive operations',
                        action='store_true',
                        default=False)
    parser.add_argument('--weights',
                        help='optional csv/kv weights for randomly filled fields. see readme.')
    cli_args = vars(parser.parse_args())

    main(cli_args)
