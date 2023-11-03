from datetime import datetime
import logging
import sys
from django.core.management.base import BaseCommand, CommandError
from reservations.helpers import ingest_csv, real_date
from reservations.models import Room, Guest, Staff
from reservations.helpers import send_email, phrasing, my_url, ingest_csv
import reservations.config as roombaht_config
from reservations.constants import ROOM_LIST
from reservations.ingest_models import RoomPlacementListIngest, ValidationError
from reservations.management import getch

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)
logger = logging.getLogger('createStaffAndRooms')

def search_ticket(ticket, guest_entries):
    while(len(guest_entries)>0):
        guest = guest_entries.pop()
        logger.debug(f'guest.ticket: {guest.ticket}, ticket: {ticket}')
        if(guest.ticket == ticket):
            return True
        else:
            continue
    return False

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

    logger.debug("read in %s rooms for %s", len(rooms_rows), hotel)

    for elem in rooms_import_list:
        room = None
        room_action = "Created"
        try:
            room = Room.objects.get(number=elem.room, name_hotel=hotel)
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
            if 'lakeview' in features or 'lake view' in features:
                room.is_lakeview = True
            if 'mountainview' in features or 'mountain view' in features:
                room.is_mountainview = True
            if 'smoking' in features:
                room.is_smoking = True

            if elem.placed_by == 'Roombaht' or \
               (elem.placed_by == '' and args['blank_is_available']):
                room.placed_by_roombot = True
                room.is_available = True
                if room.name_hotel == 'Ballys':
                    room.is_swappable = True

            if elem.art_room == 'Yes':
                room.is_art = True

            if room.name_take3 not in ROOM_LIST:
                room.is_special = True
                room.is_available = False
                room.is_swappable = False

        # check-in/check-out are only adjustable via room spreadsheet
        if elem.check_in_date == '' and args['default_check_in']:
            room.check_in = args['default_check_in']
        else:
            room.check_in = elem.check_in_date

        if elem.check_out_date == '' and args['default_check_out']:
            room.check_out = args['default_check_out']
        else:
            room.check_out = elem.check_out_date

        # room notes are only adjustable via room spreadsheet
        if elem.room_notes != room.notes:
            room.notes = elem.room_notes


        # Cannot mark a room as non available based on being set to roombaht
        #   in spreadsheet if it already actually assigned, but you can mark
        #   a room as non available/swappable if it is not assigned yet
        if elem.placed_by == '' and not room.is_available:
            if not room.guest and room.is_swappable:
                room.is_swappable = False
            else:
                logger.warning("Not marking assigned room %s as available, despite spreadsheet change", room.number)

        # the following per-guest stuff gets a bit more complex
        # TODO: Note that as we normalize names via .title() to remove chances of capitalization
        #       drama we lose the fact that some folk have mixed capitalization names i.e.
        #       Name McName and I guess we need to figure out how to handle that
        primary_name = None
        if elem.first_name_resident != '':
            primary_name = elem.first_name_resident
            if elem.last_name_resident == '':
                logger.warning("No last name for room %s", room.number)
            else:
                primary_name = f"{primary_name} {elem.last_name_resident}"

            if room.primary != primary_name.title():
                if room.guest and room.guest.transfer:
                    trans_guest = room.guest.chain()[-1]
                    if trans_guest.name == primary_name.title():
                        logger.info("Not updating primary name for room %s transfer %s", room.number, room.guest.transfer)
                    else:
                        room.primary = primary_name.title()
                else:
                    room.primary = primary_name.title()

            if elem.placed_by == '':
                logger.warning("Room %s Reserved w/o placer", room.number)

            if elem.placed_by != 'Roombaht' and elem.placed_by != '' and not room.is_placed:
                room.is_placed = True

            if elem.guest_restriction_notes != room.guest_notes:
                room.guest_notes = elem.guest_restriction_notes

            if elem.secondary_name != room.secondary:
                room.secondary = elem.secondary_name.title()

            room.available = False
        elif room.primary != '' and (not room.guest) and room.is_available:
            # Cannot unassign an already unavailable room
            room.primary = ''
            room.guest_notes = ''
            room.secondary = ''

        if elem.paying_guest == 'Comp' and not room.is_comp:
            room.is_comp = True

        if (elem.ticket_id_in_secret_party != room.sp_ticket_id
            and elem.ticket_id_in_secret_party != 'n/a'):
            room.sp_ticket_id = elem.ticket_id_in_secret_party

	# loaded room, check if room_changed
        if room.is_dirty():
            if args['dry_run']:
                dirty_msg = f"{room.name_hotel:9}{room.number:4} changes"
                for field, values in room.get_dirty_fields(verbose=True).items():
                    dirty_msg=f"{dirty_msg} {field} {values['saved']} -> {values['current']}"

                logger.warning(dirty_msg)
            else:
                room_msg = f"{room_action} {room.name_take3} room {room.number}"
                if room.is_swappable:
                    room_msg += ', swappable'

                if room.is_available:
                    room_msg += ', available'

                if room.is_placed:
                    room_msg += f", placed ({primary_name})"

                if room.is_special:
                    room_msg += ", special!"

                room.save_dirty_fields()
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

class Command(BaseCommand):
    help='Create/update rooms'

    def add_arguments(self, parser):
        parser.add_argument('rooms_file',
                            help='Path to Rooms CSV file')
        parser.add_argument('--force',
                            dest='force',
                            help='Force overwriting/updating',
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
        parser.add_argument('-d', '--dry-run',
                             help='Do not actually make changes',
                             action='store_true',
                            default=False)

    def handle(self, *args, **kwargs):
        if not kwargs['preserve']:
            if len(Room.objects.all()) > 0 or \
               len(Staff.objects.all()) > 0 or \
               len(Guest.objects.all()) > 0:
                if not kwargs['force']:
                    print('Wipe data? [y/n]')
                    if getch().lower() != 'y':
                        raise Exception('user said nope')
                else:
                    logger.warning('Wiping all data at user request!')

            Room.objects.all().delete()
            Staff.objects.all().delete()
            Guest.objects.all().delete()
        else:
            if not kwargs['force']:
                print('Update (Room) data in place (experimental!) [y/n]')
                if getch().lower() != 'y':
                    raise Exception('user said nope')
            else:
                logger.warning('Updating (room) data in place at user request!')

        create_rooms_main(kwargs)
