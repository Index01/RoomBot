import logging
import os
import sys

import django
django.setup()
from csv import DictReader, DictWriter
from reservations.models import Guest, Room
from django.forms.models import model_to_dict
from datetime import datetime

logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

logger = logging.getLogger('ReportingLogger')

ticket_file = "../samples/exampleVerifiedTickets.csv"

def read_write_reports():
    secpty_lines = []
    ticket_lines = []
    missing = []
    with open("%s/guestUpload_latest.csv" % os.environ['ROOMBAHT_TMP'], "r") as f1:
        for elem in DictReader(f1):
            secpty_lines.append(elem)

    with open(ticket_file, "r") as f2:
        for elem in DictReader(f2):
            ticket_lines.append(elem)

    for line in secpty_lines:
        ticket = line['ticket_code']
        for check_row in ticket_lines:
            if(ticket in check_row['placed'] or ticket in check_row['all_guests']):
                missing.append(f'[+] Ticket Found in both: {line} {check_row}')
                continue
            else:
                continue
            logger.debug(f'[-] Ticket not placed or excluded: {line}')
            missing.append(f'[-] Ticket not found {line}')

    with open('../output/diff_dump.md', 'w') as f3:
        for elem in missing:
            f3.write(f"{elem}\n")

def diff_latest(rows):
    diff_count = 0

    with open("%s/diff_latest.csv" % os.environ['ROOMBAHT_TMP'] , 'w') as diffout:
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
    now = datetime.now()
    ts_suffix = "%s-%s-%s-%s-%s" % (now.day, now.month, now.year, now.hour, now.minute)
    guest_dump_file = "%s/guest_dump-%s.csv" % (os.environ['ROOMBAHT_TMP'], ts_suffix)
    room_dump_file = "%s/room_dump-%s.csv" % ( os.environ['ROOMBAHT_TMP'], ts_suffix)
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
