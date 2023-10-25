
import os
import time
import logging
import jwt
import datetime
import json
import string
import sys

from csv import DictReader, DictWriter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail, EmailMessage, get_connection
from fuzzywuzzy import process, fuzz
from ..models import Staff
from ..models import Guest
from ..models import Room
from .rooms import phrasing
from ..reporting import dump_guest_rooms, diff_latest, hotel_export
from reservations.helpers import ingest_csv, phrasing, egest_csv, my_url, send_email
from reservations.constants import ROOM_LIST
import reservations.config as roombaht_config
from reservations.auth import authenticate_admin, unauthenticated
from reservations.ledger import GuestLedger

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger('ViewLogger_admin')

@api_view(['POST'])
def create_guests(request):
    guests_csv = "%s/guestUpload_latest.csv" % roombaht_config.TEMP_DIR
    if request.method == 'POST':
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

        _guest_fields, guest_rows = ingest_csv(guests_csv)

        ledger = GuestLedger(guest_rows)

        # start by seeing if we can address orphaned placed rooms
        orphan_tickets = ledger.reconcile_orphan_rooms()

        # handle basic ingestion of guests
        ledger.walk(orphan_tickets)

        lines = ledger.lines()
        logger.info("guest list uploaded by %s", auth_obj['email'])
        return Response({'csv_file': guests_csv, 'results': lines},
                        status=status.HTTP_201_CREATED)


@api_view(['POST'])
def run_reports(request):
    if request.method == 'POST':
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

        logger.info("reports being run by %s", auth_obj['email'])

        admin_emails = [admin.email for admin in Staff.objects.filter(is_admin=True)]
        guest_dump_file, room_dump_file = dump_guest_rooms()
        ballys_export_file = hotel_export('Ballys')
        attachments = [
            guest_dump_file,
            room_dump_file,
            ballys_export_file
        ]
        if os.path.exists(f"{roombaht_config.TEMP_DIR}/diff_latest.csv"):
            attachments.append(f"{roombaht_config.TEMP_DIR}/diff_latest.csv")

        if os.path.exists(f"{roombaht_config.TEMP_DIR}/guestUpload_latest.csv"):
            attachments.append(f"{roombaht_config.TEMP_DIR}/guestUpload_latest.csv")

        send_email(admin_emails,
                   'RoomService RoomBaht - Report Time',
                   'Your report(s) are here. *theme song for Brazil plays*',
                   attachments)

        return Response(str(json.dumps({"admins": admin_emails})),
                        status=status.HTTP_201_CREATED)


@api_view(['POST'])
def request_metrics(request):
    if request.method == 'POST':
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

        rooooms = Room.objects.all()
        guessssts = Guest.objects.all()

        guest_unique = len(set([guest.email for guest in guessssts]))
        guest_count = Guest.objects.all().count()
        guest_unplaced = len(guessssts.filter(room=None, ticket__isnull=True))
 
        rooms_count = rooooms.count()
        rooms_occupied = rooooms.exclude(is_available=True).count()
        rooms_swappable = rooooms.exclude(is_swappable=False).count()
        rooms_available = rooooms.exclude(is_available=False).count()
        rooms_placed_by_roombot = rooooms.exclude(placed_by_roombot=True).count()

        if(rooms_occupied!=0 and rooms_count!=0):
            percent_placed = round(float(rooms_occupied) / float(rooms_count) * 100, 2)
        else:
            percent_placed = 0

        typz = set([room.name_take3 for room in rooooms])
        room_type_totals = dict(zip(typz, [len(rooooms.filter(name_take3=typ)) for typ in typz]))
        type_totals = {f'{k}_total'.replace(' ', '_'):v for k,v in room_type_totals.items()}
        room_type_unoccupied = dict(zip(typz, [len(rooooms.filter(is_available=True, name_take3=typ)) for typ in typz]))
        type_unocc = {f'{k}_unoccupied'.replace(' ', '_'):v for k,v in room_type_unoccupied.items()}

        metrics = {"guest_count": guest_count,
                   "guest_unique": guest_unique,
                   "guest_unplaced": guest_unplaced,
                   "rooms_count": rooms_count,
                   "rooms_occupied": rooms_occupied,
                   "rooms_swappable": rooms_swappable,
                   "rooms_available": rooms_available,
                   "rooms_placed_by_roombot": rooms_placed_by_roombot,
                   "percent_placed": percent_placed,
                   }
        metrics.update(type_totals)
        metrics.update(type_unocc)
        resp = str(json.dumps(metrics))
        return Response(resp, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def guest_file_upload(request):
    if request.method == 'POST':
        data = request.data
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

        logger.info("guest data uploaded by %s", auth_obj['email'])

        rows = data['guest_list'].split('\n')
        new_guests = []
        guest_fields, guests = ingest_csv(rows)

        # basic input validation, make sure it's the right csv
        if 'ticket_code' not in guest_fields or \
           'product' not in guest_fields:
            return Response("Unknown file", status=status.HTTP_400_BAD_REQUEST)

        # build a list of products that we actually care about
        room_products = []
        for _take3_product, hotel_products in ROOM_LIST.items():
            for product in hotel_products:
                room_products.append(product)

        for guest in guests:
            # if we don't know the product, drop it
            if guest['product'] not in room_products:
                logger.debug("Ticket %s has product we don't care about: %s",
                             guest['ticket_code'],
                             guest['product'])
                continue

            # if the ticket already is in the system, drop it
            existing_ticket = None

            try:
                existing_ticket = Guest.objects.get(ticket=guest['ticket_code'])
            except Guest.DoesNotExist:
                pass

            if existing_ticket:
                logger.warning("[-] Ticket %s from upload already in db", guest['ticket_code'])
                continue

            new_guests.append(guest)

        # write out the csv for future use
        egest_csv(new_guests,
                  guest_fields,
                  f"{roombaht_config.TEMP_DIR}/guestUpload_latest.csv")

        first_row = {}
        if len(new_guests) > 0:
            first_row = new_guests[0]

        resp = str(json.dumps({"received_rows": len(guests),
                               "valid_rows": len(new_guests),
                               "diff": diff_latest(new_guests),
                               "headers": guest_fields,
                               "first_row": first_row,
                               "status": "Ready to Load..."
                               }))

        return Response(resp, status=status.HTTP_201_CREATED)
