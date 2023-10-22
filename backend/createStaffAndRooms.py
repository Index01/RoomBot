import argparse
import logging
import os
import random
import termios
import tty
import string
import sys

import django
django.setup()
from reservations.models import Guest, Room, Staff
from django.forms.models import model_to_dict
from django.utils.dateparse import parse_date
from reservations.helpers import phrasing, ingest_csv, my_url, send_email
import reservations.config as roombaht_config
from reservations.constants import ROOM_LIST
from datetime import datetime

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger('createStaffAndRooms')

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

def search_ticket(ticket, guest_entries):
    while(len(guest_entries)>0):
        guest = guest_entries.pop()
        logger.debug(f'guest.ticket: {guest.ticket}, ticket: {ticket}')
        if(guest.ticket == ticket):
            return True
        else:
            continue
    return False


def real_date(a_date):
    day, date = a_date.split('-')
    month, day = date.lstrip().split('/')
    return parse_date("%s-%s-%s" % (datetime.now().year, month, day))

def create_rooms_main(rooms_file, is_hardrock=False, force_roombaht=False):
    rooms={}
    _rooms_fields, rooms_rows = ingest_csv(rooms_file)

    if(is_hardrock):
        hotel = "Hard Rock"
    else:
        hotel = "Ballys"

    logger.info("read in %s rooms for %s", len(rooms_rows), hotel)

    for elem in rooms_rows:
        room = None
        room_changed = False
        room_action = "Created"
        try:
            room = Room.objects.get(number=elem['Room'])
            room_action = "Updated"
        except Room.DoesNotExist:
            # some things are not mutable
            # * room features
            # * room number
            # * hotel
            # * room type
            # * initial roombaht based availability
            room = Room(name_take3=elem['Room Type'],
                        name_hotel=hotel,
                        number=elem['Room']
                        )

            try:
                features = elem['Room Features (Accessibility, Lakeview, Smoking)'].lower()
            except KeyError as e:
                features = []
            if 'hearing accessible' in features:
                room.is_hearing_accessible = True

            if 'ada' in features:
                room.is_ada = True

            if 'lakeview' in features:
                room.is_lakeview = True

            if 'smoking' in features:
                room.is_smoking = True

            if elem['Placed By'] == 'Roombaht' or \
               (elem['Placed By'] == '' and force_roombaht):
                room.is_available = True
                room.is_swappable = True

            if elem['Art Room'] == 'Yes':
                room.is_art = True

            if len([x for x in ROOM_LIST.keys() if x == room.name_take3]) == 0:
                room.is_special = True
                room.is_available = False
                room.is_swappable = False

            room_changed = True

        # check-in/check-out are only adjustable via room spreadsheet
        if elem['Check-in Date'] != '':
            check_in_date = real_date(elem['Check-in Date'])
            if check_in_date != room.check_in:
                room.check_in = check_in_date
                room_changed = True
        elif elem['Check-in Date'] == '' and room.check_in is not None:
            room.check_in = None
            room_changed = True

        if elem['Check-out Date'] != '':
            check_out_date = real_date(elem['Check-out Date'])
            if check_out_date != room.check_out:
                room.check_out = check_out_date
                room_changed = True
        elif elem['Check-out Date'] == '' and room.check_out is not None:
            room.check_out = None
            room_changed = True

        # room notes are only adjustable via room spreadsheet
        if elem['Room Notes'] != room.notes:
            room.notes = elem['Room Notes']
            room_changed = True

        # Cannot mark a room as non available based on being set to roombaht
        #   in spreadsheet if it already actually assigned, but you can mark
        #   a room as non available/swappable if it is not assigned yet
        if elem['Placed By'] == '' and (not room.is_available):
            if not room.guest:
                room.is_available = False
                room.is_swappable = False
                room_changed = True
            else:
                logger.warning("Not marking assigned room %s as available, despite spreadsheet change", room.number)

        # the following per-guest stuff gets a bit more complex
        primary_name = None
        if elem['First Name (Resident)'] != '':
            primary_name = elem['First Name (Resident)']
            if elem['Last Name (Resident)'] == '':
                logger.warning("No last name for room %s", room.number)
            else:
                primary_name = f"{primary_name} {elem['Last Name (Resident)']}"

            if room.primary != primary_name:
                room.primary = primary_name.capitalize()
                room_changed = True

            if elem['Placed By'] == '':
                logger.warning("Room %s Reserved w/o placer", room.number)

            if elem['Placed By'] != 'Roombaht' and elem['Placed By'] != '' and not room.is_placed:
                room.is_placed = True
                room_changed = True

            if elem['Guest Restriction Notes'] != room.guest_notes:
                room.guest_notes = elem['Guest Restriction Notes']
                room_changed = True

            if elem['Secondary Name'] != room.secondary:
                room.secondary = elem['Secondary Name'].capitalize()
                room_changed = True

            room.available = False
        elif room.primary != '' and (not room.guest) and room.is_available:
            # Cannot unassign an already unavailable room
            room.primary = ''
            room.guest_notes = ''
            room.secondary = ''
            room_changed = True

        if elem['Paying guest?'] == 'Comp' and not room.is_comp:
            room.is_comp = True
            room_changed = True

        if elem['Ticket ID in SecretParty'] != room.sp_ticket_id \
           and elem['Ticket ID in SecretParty'] != 'n/a':
            room.sp_ticket_id = elem['Ticket ID in SecretParty']
            room_changed = True

        if room_changed:
            room_msg = f"{room_action} {room.name_take3} room {room.number}"
            if room.is_swappable:
                room_msg += ", swappable"

            if not room.is_available:
                room_msg += f", placed ({primary_name})"

            room.save()
            logger.debug(room_msg)

            # build up some ingestion metrics
            room_count_obj = None
            if room.name_take3 not in rooms:
                room_count_obj = {
                    'count': 1,
                    'available': 0,
                    'swappable': 0,
                    'art': 0
                }
            else:
                room_count_obj = rooms[room.name_take3]
                room_count_obj['count'] += 1

            if room.is_available:
                room_count_obj['available'] += 1

            if room.is_swappable:
                room_count_obj['swappable'] += 1

            if room.is_art:
                room_count_obj['art'] += 1

            rooms[room.name_take3] = room_count_obj

        else:
            logger.debug("No changes to room %s", room.number)

    total_rooms = 0
    available_rooms = 0
    swappable_rooms = 0
    art_rooms = 0
    for r_counts, counts in rooms.items():
        logger.info("room %s total:%s, available:%s, swappable:%s, art:%s",
                    r_counts,
                    counts['count'],
                    counts['available'],
                    counts['swappable'],
                    counts['art'])

        total_rooms += counts['count']
        available_rooms += counts['available']
        swappable_rooms += counts['swappable']
        art_rooms += counts['art']

    logger.info("total:%s, available:%s, placed:%s, swappable:%s, art:%s",
             total_rooms, available_rooms, total_rooms - available_rooms,
             swappable_rooms, art_rooms)

def create_staff(init_file):
    _staff_fields, staff = ingest_csv(init_file)

    for staff_new in staff:
        existing_staff = None
        try:
            existing_staff = Staff.objects.get(email = staff_new['email'])
        except Staff.DoesNotExist:
            pass

        if existing_staff:
            logger.debug("Staff %s already exists", existing_staff.email)
            continue

        otp = phrasing()
        guest=Guest(name=staff_new['name'],
            email=staff_new['email'],
            jwt=otp)
        guest.save()

        staff=Staff(name=staff_new['name'],
            email=staff_new['email'],
            guest=guest,
            is_admin=staff_new['is_admin'])
        staff.save()

        logger.info("Created staff: %s, admin: %s", staff_new['name'], staff_new['is_admin'])

        hostname = my_url()

        body_text = f"""
                Congratulations, u have been deemed Staff worthy material.

                Email {staff_new['email']}
                Admin {otp}

                login at {hostname}/login
                then go to {hostname}/admin
                Good Luck, Starfighter.

        """
        send_email([staff_new['email']],
                    'RoomService RoomBaht - Staff Activation',
                    body_text)


def main(args):

    if not args['preserve']:
        if len(Room.objects.all()) > 0 or \
           len(Staff.objects.all()) > 0 or \
           len(Guest.objects.all()) > 0:
            if not args['force']:
                print('Overwrite data? [y/n]')
                if getch().lower() != 'y':
                    raise Exception('user said nope')
            else:
                logger.warning('Overwriting data at user request!')

        Room.objects.all().delete()
        Staff.objects.all().delete()
        Guest.objects.all().delete()
    else:
        if not args['force']:
            print('Update data in place (experimental!) [y/n]')
            if getch().lower() != 'y':
                raise Exception('user said nope')
        else:
            logger.warning('Updating data in place at user request!')

    create_rooms_main(args['rooms_file'], is_hardrock=args['hardrock'], force_roombaht=args['blank_is_available'])
    create_staff(args['staff_file'])

if __name__=="__main__":
    parser = argparse.ArgumentParser(usage=('like db fixtures but not'),
                                     description='create staff and rooms')
    parser.add_argument('rooms_file',
                        help='Path to Rooms CSV file')
    parser.add_argument('staff_file',
                        help='Path to Staff CSV file')
    parser.add_argument('--force',
                        dest='force',
                        help='Force overwriting',
                        action='store_true',
                        default=False)
    parser.add_argument('--hard-rock',
                        dest='hardrock',
                        action='store_true',
                        default=False,
                        help='Not Ballys')
    parser.add_argument('--preserve',
                        dest='preserve',
                        action='store_true',
                        default=False,
                        help='Preserve data, updating rooms in place')
    parser.add_argument('--blank-placement-is-available',
                        dest='blank_is_available',
                        action='store_true',
                        default=False,
                        help='When set it treats blank "Placed By" fields as available rooms')
    args = vars(parser.parse_args())
    main(args)
