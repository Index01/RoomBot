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
from reservations.helpers import phrasing, ingest_csv
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

def create_rooms_main(rooms_file, is_hardrock=False):
    rooms=[]
    _rooms_fields, rooms_rows = ingest_csv(rooms_file)

    if(is_hardrock):
        hotel = "Hard Rock"
    else:
        hotel = "Ballys"

    logger.info("read in %s rooms for %s", len(rooms_rows), hotel)

    for elem in rooms_rows:
        a_room = Room(name_take3=elem['Room Type'],
                      name_hotel=hotel,
                      number=elem['Room']
                      )

        # these things are always going to be consistent per room
        if elem['Check-in Date'] != '':
            a_room.check_in = real_date(elem['Check-in Date'])

        if elem['Check-out Date'] != '':
            a_room.check_out = real_date(elem['Check-out Date'])

        features = elem['Room Features (Accesbility, Lakeview, Smoking)(not visible externally)'].lower()
        if 'hearing accessible' in features:
            a_room.is_hearing_accessible = True

        if 'ada' in features:
            a_room.is_ada = True

        if 'lakeview' in features:
            a_room.is_lakeview = True

        if 'smoking' in features:
            a_room.is_smoking = True

        if len(elem['Room Notes']) > 0:
            a_room.notes = elem['Room Notes']

        if elem['Changeable'] == '' or \
           'yes' in elem['Changeable'].lower():
            a_room.is_swappable = True

        if elem['Placed By'] == 'Roombaht':
            a_room.is_available = True

        # the following per-guest stuff gets a bit more complex
        if elem['First Name (Resident)'] != '':
            primary_name = elem['First Name (Resident)']
            if elem['Last Name (Resident)'] == '':
                logger.warning("No last name for room %s", a_room.number)
            else:
                primary_name = "%s %s" % (primary_name, elem['Last Name (Resident)'])

            a_room.primary = primary_name

            if elem['Placed By'] == '':
                logger.warning("Reserved w/o placer for room %s", a_room.number)

            if elem['Guest Restriction Notes'] != '':
                a_room.guest_notes = elem['Guest Restriction Notes']

            if elem['Secondary Name'] != '':
                a_room.secondary = elem['Secondary Name']

            a_room.available = False

        if elem['Ticket ID in SecretParty'] != '':
            a_room.sp_ticket_id = elem['Ticket ID in SecretParty']

        room_msg = "Created room %s" % a_room.number
        if a_room.is_swappable:
            room_msg += ", swappable"

        if not a_room.is_available:
            room_msg += ", placed"

        rooms.append(a_room)
        a_room.save()
        logger.info(room_msg)

    swappable_rooms = [x for x in rooms if x.is_swappable]
    logger.info("created %s rooms of which %s are swappable",
                 len(rooms),
                 len(swappable_rooms))


def create_staff(init_file):
    _staff_fields, staff = ingest_csv(init_file)

    for staff_new in staff:
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

        hostname = os.environ['ROOMBAHT_HOST']

        if os.environ.get('ROOMBAHT_SEND_MAIL', 'FALSE').lower() == 'true':
            logger.debug(f'[+] Sending invite for staff member {staff_new["email"]}')

            body_text = f"""
                Congratulations, u have been deemed Staff worthy material.

                Email {staff_new['email']}
                Admin {otp}

                login at http://{hostname}/login
                then go to http://{hostname}/admin
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

    create_rooms_main(args['rooms_file'], is_hardrock=args['hardrock'])
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

    args = vars(parser.parse_args())
    main(args)
