import logging
import os
import sys
from datetime import datetime

import django
django.setup()
from csv import DictReader, DictWriter
from reservations.models import Guest, Room
from django.forms.models import model_to_dict
from reservations.helpers import ts_suffix, egest_csv, take3_date
import reservations.config as roombaht_config

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger(__name__)


def diff_swaps(swap_from, swap_to):
    fieldnames = ['Datetime', 'Swap From', 'Swap To']
    file = f"{roombaht_config.TEMP_DIR}/diff_swaps.csv"
    file_exists = os.path.isfile(file)
    with open(file, 'a') as diffout:
        writer = DictWriter(diffout, fieldnames)
        if(not file_exists):
            writer.writeheader()
        writer.writerow({'Datetime': datetime.now(), 'Swap From': swap_from.number, 'Swap To': swap_to.number})

def diff_swaps_count():
    try:
        with open(f"{roombaht_config.TEMP_DIR}/diff_swaps.csv", 'r') as diffout:
            return sum(1 for lie in diffout) - 1
    except FileNotFoundError as e:
        logger.warn(f'No swaps yet')
        return 0

def diff_latest(rows):
    diff_count = 0

    with open(f"{roombaht_config.TEMP_DIR}/diff_latest.csv", 'w') as diffout:
        guests = Guest.objects.all()
        diffout.write("Things in latest guest list upload but not in the db\n")
        for row in rows:
            existing_ticket = None
            try:
                existing_ticket = Guest.objects.get(ticket=row['ticket_code'])
            except Guest.DoesNotExist:
                pass

            if not existing_ticket:
                diff_count+=1
                diffout.write("%s,%s %s,%s\n" % (row['ticket_code'],
                                               row['first_name'],
                                               row['last_name'],
                                               row['email']))

        diffout.write("Things in db but not in most recent guest list upload\n")
        for guest in guests:
            ticket_found = False
            for row in rows:
                if guest.ticket == row['ticket_code']:
                    ticket_found = True
                    break

            if ticket_found:
                diff_count+=1
                diffout.write(f'{guest.ticket},{guest.name},{guest.email}\n')

    return diff_count

def dump_guest_rooms():
    guest_dump_file = f"{roombaht_config.TEMP_DIR}/guest_dump-{ts_suffix()}.csv"
    room_dump_file = f"{roombaht_config.TEMP_DIR}/room_dump-{ts_suffix()}.csv"
    guests = Guest.objects.all()
    logger.debug(f'[-] dumping guests and room tables')
    with open(guest_dump_file, 'w+') as guest_file:
        header = [field.name for field in guests[0]._meta.fields if field.name!="jwt" and field.name!="invitation"]
        writer = DictWriter(guest_file, fieldnames=header)
        writer.writeheader()
        for guest in guests:
            data = model_to_dict(guest, fields=[field.name for field in guest._meta.fields if field.name!="jwt" and field.name!="invitation"])
            writer.writerow(data)

    rooms = Room.objects.all()
    with open(room_dump_file, 'w+') as room_file:
        header = [field.name for field in rooms[0]._meta.fields if field.name!="swap_code" and field.name!="swap_time"]
        writer = DictWriter(room_file, fieldnames=header)
        writer.writeheader()
        for room in rooms:
            data = model_to_dict(room, fields=[field.name for field in room._meta.fields if field.name!="swap_code" and field.name!="swap_time"])
            writer.writerow(data)

    logger.debug(f'[-] rooms done')
    return guest_dump_file, room_dump_file

def hotel_export(hotel):
    fields = [
        'room_number',
        'room_type',
        'check_in',
        'check_out',
        'primary_name',
        'secondary_name'
    ]
    rooms = Room.objects.filter(name_hotel = hotel.title())
    if rooms.count() == 0:
        raise Exception("No rooms found for hotel %s" % hotel)

    rows = []
    for room in rooms:
        # some validation

        row = {
            'room_number': room.number,
            'room_type': room.hotel_sku(),
            'primary_name': room.primary
        }
        if room.check_in and room.check_out:
            row['check_in'] = room.check_in
            row['check_out'] = room.check_out
        elif room.check_in and not room.check_out:
            logger.warning("Room %s missing check out date", room.number)
            row['check_in'] = room.check_in
            row['check_out'] = 'TBD'
        elif room.check_out and not room.check_in:
            logger.warning("Room %s missing check in date", room.number)
            row['check_in'] = 'TBD'
            row['check_out'] = room.check_out
        else:
            row['check_in'] = 'TBD'
            row['check_out'] = 'TBD'

        if room.secondary != '':
            row['secondary_name'] = room.secondary

        rows.append(row)

    hotel_export_file = f"{roombaht_config.TEMP_DIR}/hotel_{hotel.lower()}_export-{ts_suffix()}.csv"

    egest_csv(rows, fields, hotel_export_file)
    return hotel_export_file


def rooming_list_export(hotel):
    rooms = Room.objects.filter(name_hotel = hotel.title())
    if rooms.count() == 0:
        msg = "No rooms found for hotel %s" % hotel
        raise Exception("No rooms found for hotel %s" % hotel)

    cols = [
        "room",
        "room_type",
        "room_number",
        "first_name",
        "last_name",
        "secondary_name",
        "check_in_date",
        "check_out_date",
        "placed_by_roombaht",
        "is_comp",
        "sp_ticket_id",
        "guest_notes",
        "is_art",
        "paying_guest"
    ]

    rows = []
    for room in rooms:
        # hacky split to first/last name
        primary_name = room.primary.split(" ", 1)
        first_name = primary_name[0]
        last_name = primary_name[1] if len(primary_name)>1 else ""
        row = {
            'room_number': room.number,
            'room_type': room.hotel_sku(),
            'first_name': first_name,
            'last_name': last_name,
        }
        if room.secondary != '':
            row['secondary_name'] = room.secondary
        if room.check_in and room.check_out:
            row['check_in_date'] = take3_date(room.check_in)
            row['check_out_date'] = take3_date(room.check_out)
        elif room.check_in and not room.check_out:
            logger.warning("Room %s missing check out date", room.number)
            row['check_in_date'] = take3_date(room.check_in)
            row['check_out_date'] = 'TBD'
        elif room.check_out and not room.check_in:
            logger.warning("Room %s missing check in date", room.number)
            row['check_in_date'] = 'TBD'
            row['check_out_date'] = take3_date(room.check_out)
        else:
            row['check_in_date'] = 'TBD'
            row['check_out_date'] = 'TBD'
        row["placed_by_roombaht"] = room.placed_by_roombot
        row["paying_guest"] = "Comp" if room.is_comp else "Yes"
        if room.sp_ticket_id and not room.is_comp:
            row['sp_ticket_id'] = room.sp_ticket_id
        elif room.is_comp:
            row['sp_ticket_id'] = "n/a"
        else:
            # shouldnt have any of these, but here we are
            logger.warning(f"No SP ticket state found for room: {room.number}")
            row['sp_ticket_id'] = ""
        row["guest_notes"] = room.guest_notes
        row["is_art"] = room.is_art

        rows.append(row)

    rooming_list_export_file = f"{roombaht_config.TEMP_DIR}/hotel_{hotel.lower()}_export-{ts_suffix()}.csv"

    egest_csv(rows, cols, rooming_list_export_file)
    return rooming_list_export_file
