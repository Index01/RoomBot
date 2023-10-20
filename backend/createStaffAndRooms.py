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
from django.core.mail import send_mail
from django.core.mail import EmailMessage, get_connection
from django.forms.models import model_to_dict
from django.utils.dateparse import parse_date
from reservations.helpers import phrasing, ingest_csv, my_url
from datetime import datetime

logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

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
    rooms=[]
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

            features = elem['Room Features (Accessibility, Lakeview, Smoking)'].lower()
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

        if (elem['Changeable'] == '' or 'yes' in elem['Changeable'].lower()) and \
           not room.is_swappable:
            room.is_swappable = True
            room_changed = True
        elif elem['Changeable'].lower() == 'no' and room.is_swappable:
            room.is_swappable = False
            room_changed = True

        # Cannot mark a room as non available based on being set to roombaht
        #   in spreadsheet if it already actually assigned
        if elem['Placed By'] == '' and (not room.is_available):
            if not room.guest:
                room.is_available = False
                room_changed = True
            else:
                logger.warning("Not marking assigned room %s as available, despite spreadsheet change", room.number)

        # the following per-guest stuff gets a bit more complex
        if elem['First Name (Resident)'] != '':
            primary_name = elem['First Name (Resident)']
            if elem['Last Name (Resident)'] == '':
                logger.warning("No last name for room %s", room.number)
            else:
                primary_name = f"{primary_name} {elem['Last Name (Resident)']}"

            if room.primary != primary_name:
                room.primary = primary_name
                room_changed = True

            if elem['Placed By'] == '':
                logger.warning("Room %s Reserved w/o placer", room.number)

            if elem['Guest Restriction Notes'] != room.guest_notes:
                room.guest_notes = elem['Guest Restriction Notes']
                room_changed = True

            if elem['Secondary Name'] != room.secondary:
                room.secondary = elem['Secondary Name']
                room_changed = True

            room.available = False
        elif room.primary != '' and (not room.guest) and room.is_available:
            # Cannot unassign an already unavailable room
            room.primary = ''
            room.guest_notes = ''
            room.secondary = ''
            room_changed = True

        if elem['Ticket ID in SecretParty'] != room.sp_ticket_id:
            room.sp_ticket_id = elem['Ticket ID in SecretParty']
            room_changed = True

        if room_changed:
            room_msg = f"{room_action} room {room.number}"
            if room.is_swappable:
                room_msg += ", swappable"

            if not room.is_available:
                room_msg += ", placed"

            rooms.append(room)
            room.save()

            logger.debug(room_msg)
        else:
            logger.debug("No changes to room %s", room.number)

    swappable_rooms = [x for x in rooms if x.is_swappable]
    logger.info("updated %s rooms of which %s are swappable",
                len(rooms),
                len(swappable_rooms))


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
            ticket=666,
            jwt=otp)
        guest.save()

        staff=Staff(name=staff_new['name'],
            email=staff_new['email'],
            guest=guest,
            is_admin=staff_new['is_admin'])
        staff.save()

        logger.info(f"[+] Created staff: {staff_new['name']}, {staff_new['email']}, otp: {otp}, isadmin: {staff_new['is_admin']}")

        hostname = my_url()

        if os.environ.get('ROOMBAHT_SEND_MAIL', 'FALSE').lower() == 'true':
            logger.debug(f'[+] Sending invite for staff member {staff_new["email"]}')

            body_text = f"""
                Congratulations, u have been deemed Staff worthy material.

                Email {staff_new['email']}
                Admin {otp}

                login at {hostname}/login
                then go to {hostname}/admin
                Good Luck, Starfighter.

            """
            send_mail("RoomService RoomBaht",
                      body_text,
                      os.environ['ROOMBAHT_EMAIL_HOST_USER'],
                      [staff_new["email"]],
                      auth_user=os.environ['ROOMBAHT_EMAIL_HOST_USER'],
                      auth_password=os.environ['ROOMBAHT_EMAIL_HOST_PASSWORD'],
                      fail_silently=False)


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
