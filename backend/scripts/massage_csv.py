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
from lorem_text.lorem import words as lorem_words

from backend.reservations.ingest_models import SecretPartyGuestIngest, RoomPlacementListIngest

# don't judge
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from reservations.helpers import phrasing, ingest_csv, egest_csv

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
        random_name = list(guest_names.keys())[randint(0, len(guest_names) - 1)]
        placers.append(guest_names[random_name])

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

def massage_rooms(input_items, maps, weights):
    name_maps, email_maps = maps
    output_items = []

    guest_names = [x for x, y in name_maps.items()]

    get_placer = random_placer(name_maps)
    art_type = art_room_types()

    for item in input_items:
        real_name = "%s %s" % (item['First Name (Resident)'], item['Last Name (Resident)'])

        if real_name not in name_maps.keys():
            new_name = generate_name(style = 'capital')
            name_maps[real_name] = new_name
            new_name_bits = new_name.split(' ')
        else:
            new_name_bits = name_maps[real_name].split(' ')

        new_first_name = new_name_bits[0]
        new_last_name = new_name_bits[1]

        new_item = {
            'Placement Verified': item['Placement Verified'],
            'Floor': item['Floor'],
            'Room': item['Room'],
            'Room Type': item['Room Type'],
            'Room Features (Accessibility, Lakeview, Smoking)': item['Room Features (Accessibility, Lakeview, Smoking)'],
            'Connected To Room': item['Connected To Room'],
            'Room Owned By (Secret Party)': item['Room Owned By (Secret Party)'],
            'Check-in Date': item['Check-in Date'],
            'Check-out Date': item['Check-out Date'],
            'Change Reason': item['Change Reason'],
            'Guest Restriction Notes': item['Guest Restriction Notes'],
            'Placement Team Notes': item['Placement Team Notes'],
            'Paying guest?': item['Paying guest?'],
            'Department': item['Department'],
            'Ticket ID in SecretParty': item['Ticket ID in SecretParty']
        }

        # straight anonymization of pii
        if weights is None:
            if item['Placed By'] != '' and item['Placed By'] != 'Roombaht':
                if item['Placed By'] not in name_maps:
                    new_placer = generate_name(style = 'capital')
                    name_maps[item['Placed By']] = new_placer
                    new_item['Placed By'] = new_placer
                else:
                    new_item['Placed By'] = name_maps[item['Placed By']]

            if item['First Name (Resident)'] != '':
                new_item['First Name (Resident)'] = new_first_name
            if item['Last Name (Resident)'] != '':
                new_item['Last Name (Resident)'] = new_last_name

            if item['Secondary Name'] != '':
                if item['Secondary Name'] not in name_maps:
                    new_secondary = generate_name(style = 'capital')
                    name_maps[item['Secondary Name']] = new_secondary
                    new_item['Secondary Name'] = new_secondary
                else:
                    new_item['Secondary Name'] = name_maps[item['Secondary Name']]

            if item['Art Room'].lower() == 'yes':
                new_item['Art Room'] = item['Art Room']
                new_item['Art Name / Placed Name'] = phrasing()
                new_item['Art Room Type'] = art_type()

            if item['Changeable'] != '':
                if 'yes' in item['Changeable'].lower():
                    new_item['Changeable'] = 'Yes'
                else:
                    new_item['Changeable'] = 'No'

            if 'Placed By' not in new_item:
                new_item['Placed By'] = 'Roombaht'

        # add some randomness here for more test data
        else:
            if randint(1, 100) <= weights.get('placed', 10):
                new_item['Placed By'] = get_placer()
                new_item['First Name (Resident)'] = new_first_name
                new_item['Last Name (Resident)'] = new_last_name
                if randint(1,100) <= weights.get('secondary', 50):
                    new_item['Secondary Name'] = guest_names[randint(0, len(guest_names) - 1)]

            if randint(1, 100) <= weights.get('art', 5):
                if 'Placed By' not in new_item:
                    new_item['Placed By'] = get_placer()

                new_item['Art Room'] = 'Yes'
                new_item['Art Name / Placed Name'] = phrasing()
                new_item['Art Room Type'] = art_type()
            else:
                new_item['Art Room'] = 'No'

            if 'Placed By' in new_item:
                if randint(1, 100) <= weights.get('changeable', 50):
                    new_item['Changeable'] = 'Yes'
                else:
                    new_item['Changeable'] = 'No'
            else:
                new_item['Placed By'] = 'Roombaht'


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
            'ticket_code': item['ticket_code'],
            'last_name': new_last_name,
            'first_name': new_first_name,
            'email': email_maps[item['email']],
            'product': item['product']
        }

        if item['transferred_from_code'] != '':
            new_item['transferred_from_code'] = item['transferred_from_code']

        output_items.append(new_item)

    return [name_maps, email_maps], output_items

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

    weights = None
    if args['random']:
        weights = parse_weights(args['weights'])

    guest_fields, original_guests = ingest_csv(src_guest_list)
    room_fields, original_rooms = ingest_csv(src_room_list)
    # validate the csv ingests
    original_guests_valid = [SecretPartyGuestIngest(**guest) for guest in original_guests]
    original_rooms_valid = [RoomPlacementListIngest(**room) for room in original_rooms]

    maps, anon_guests = massage_guests(original_guests_valid)
    anon_rooms = massage_rooms(original_rooms_valid, maps, weights)

    egest_csv(anon_guests, guest_fields, dest_guest_list)
    egest_csv(anon_rooms, room_fields, dest_room_list)

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
    parser.add_argument('--random',
                        help='Make weighted random changes to rooms',
                        action='store_true',
                        default=False)
    cli_args = vars(parser.parse_args())

    main(cli_args)
