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
from reservations.ingest_models import RoomPlacementListIngest, ValidationError

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


def real_date(a_date: str, year=None):
    """Convert string date into python date

    Args:
        a_date (str): date string,
            expected format: "Mon - 11/7", "11/7"
        year (Optional[int]): year, in 4-digit format
            Allows specification of year, otherwise is in current year at runtime
    Returns:
        date: python `date` object
    """
    year = year or datetime.now().year
    date_bits = a_date.split("-")
    date = None
    if len(date_bits) == 1:
        date = date_bits[0]
    elif len(date_bits) == 2:
        date = date_bits[1]
    else:
        raise Exception(f"Unexpected date format {a_date}")

    month, day = date.lstrip().split('/')
    return parse_date("%s-%s-%s" % (year, month, day))

def create_rooms_main(args):
    rooms_file = args['rooms_file']
    hotel = None
    if args['hotel_name'] == 'ballys':
        hotel = "Ballys"
    elif args['hotel_name'] == 'hardrock':
        hotel = 'Hard Rock'
    else:
        raise Exception(f"Unknown hotel name {args['hotel_name']}specified")

    rooms={}
    _rooms_fields, rooms_rows = ingest_csv(rooms_file)
    rooms_import_list = []
    for r in rooms_rows:
        try:
            room_data = RoomPlacementListIngest(**r)
            rooms_import_list.append(room_data)
        except ValidationError as e:
            logger.warning("Validation error for row %s", e)

    logger.info("read in %s rooms for %s", len(rooms_rows), hotel)

    for elem in rooms_import_list:
        room = None
        room_changed = False
        room_action = "Created"
        try:
            room = Room.objects.get(number=elem.room)
            room_action = "Updated"
        except Room.DoesNotExist:
            # some things are not mutable
            # * room features
            # * room number
            # * hotel
            # * room type
            # * initial roombaht based availability
            room = Room(name_take3=elem.room_type,
                        name_hotel=hotel,
                        number=elem.room)

            try:
                features = elem.room_features.lower()
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

            if elem.placed_by == 'Roombaht' or \
               (elem.placed_by == '' and args['blank_is_available']):
                room.is_available = True
                room.is_swappable = True
                room.placed_by_roombot = True

            if elem.art_room == 'Yes':
                room.is_art = True

            if len([x for x in ROOM_LIST.keys() if x == room.name_take3]) == 0:
                room.is_special = True
                room.is_available = False
                room.is_swappable = False

            room_changed = True

        # check-in/check-out are only adjustable via room spreadsheet
        if elem.check_in_date != '':
            check_in_date = real_date(elem.check_in_date)
            if check_in_date != room.check_in:
                room.check_in = check_in_date
                room_changed = True
        elif elem.check_in_date == '' and room.check_in is not None:
            room.check_in = None
            room_changed = True
        elif elem.check_in_date == '' and room.check_in is None:
            check_in_date = real_date(args['default_check_in'])
            room.check_in = check_in_date
            room_changed = True

        if elem.check_out_date != '':
            check_out_date = real_date(elem.check_out_date)
            if check_out_date != room.check_out:
                room.check_out = check_out_date
                room_changed = True
        elif elem.check_out_date == '' and room.check_out is not None:
            room.check_out = None
            room_changed = True
        elif elem.check_out_date == '' and room.check_out is None:
            check_out_date = real_date(args['default_check_out'])
            room.check_out = check_out_date
            room_changed = True

        # room notes are only adjustable via room spreadsheet
        if elem.room_notes != room.notes:
            room.notes = elem.room_notes
            room_changed = True


        # Cannot mark a room as non available based on being set to roombaht
        #   in spreadsheet if it already actually assigned, but you can mark
        #   a room as non available/swappable if it is not assigned yet
        if elem.placed_by == '' and (not room.is_available):
            if not room.guest:
                room.is_available = False
                room.is_swappable = False
                room_changed = True
            else:
                logger.warning("Not marking assigned room %s as available, despite spreadsheet change", room.number)

        # the following per-guest stuff gets a bit more complex
        primary_name = None
        if elem.first_name_resident != '':
            primary_name = elem.first_name_resident
            if elem.last_name_resident == '':
                logger.warning("No last name for room %s", room.number)
            else:
                primary_name = f"{primary_name} {elem.last_name_resident}"

            if room.primary != primary_name:
                room.primary = primary_name.title()
                room_changed = True

            if elem.placed_by == '':
                logger.warning("Room %s Reserved w/o placer", room.number)

            if elem.placed_by != 'Roombaht' and elem.placed_by != '' and not room.is_placed:
                room.is_placed = True
                room_changed = True

            if elem.guest_restriction_notes != room.guest_notes:
                room.guest_notes = elem.guest_restriction_notes
                room_changed = True

            if elem.secondary_name != room.secondary:
                room.secondary = elem.secondary_name.title()
                room_changed = True

            room.available = False
        elif room.primary != '' and (not room.guest) and room.is_available:
            # Cannot unassign an already unavailable room
            room.primary = ''
            room.guest_notes = ''
            room.secondary = ''
            room_changed = True

        if elem.paying_guest == 'Comp' and not room.is_comp:
            room.is_comp = True
            room_changed = True

        if (elem.ticket_id_in_secret_party != room.sp_ticket_id
            and elem.ticket_id_in_secret_party != 'n/a'):
            room.sp_ticket_id = elem.ticket_id_in_secret_party
            room_changed = True

	# loaded room, check if room_changed
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

    create_rooms_main(args)
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
    parser.add_argument('--hotel-name',
                        default="ballys",
                        help='Specify hotel name (ballys, hardrock)')
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
    parser.add_argument('--default-check-in',
                        help='Default check in date MM/DD')
    parser.add_argument('--default-check-out',
                        help='Default check out date MM/DD')
    args = vars(parser.parse_args())
    main(args)
