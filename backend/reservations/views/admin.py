
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
from ..models import Staff
from ..models import Guest
from ..models import Room
from .rooms import phrasing
from ..reporting import dump_guest_rooms, diff_latest, hotel_export
from reservations.helpers import ingest_csv, phrasing, egest_csv, my_url, send_email
from reservations.constants import ROOM_LIST
import reservations.config as roombaht_config
from reservations.auth import authenticate_admin, unauthenticated

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger('ViewLogger_admin')

def onboarding_email(guest_new, otp):
    if not roombaht_config.SEND_ONBOARDING:
        return

    hostname = my_url()
    time.sleep(5)
    body_text = f"""
        BleepBloopBleep, this is the Room Service RoomBaht for Room Swaps letting you know the floors have been cleaned and you have been assigned a room. No bucket or mop needed.

        After you login below you can view your current room, look at other rooms and send trade requests. This functionality is only available until Monday 11/7 at 5pm PST, so please make sure you are good with what you have or trade early.

        Goes without saying, but don't forward this email.

        This is your password, there are many like it but this one is yours. Once you use this password on a device, RoomBaht will remember you, but only on that device.
        Copy and paste this password. Because let’s face it, no one should trust humans to make passwords:
        {otp}
        {hostname}/login

        Good Luck, Starfighter.

    """
    send_email([guest_new["email"]],
               'RoomService RoomBaht - Account Activation',
               body_text)

def find_room(room_product):
    room_type = None
    for a_type, a_products in ROOM_LIST.items():
        for a_product in a_products:
            if a_product == room_product:
                room_type = a_type
                break

    if not room_type:
        raise Exception("Unable to actually find room type for %s" % room_product)

    available_room = Room.objects \
                         .filter(is_available=True,
                                 name_take3=room_type
                                 ) \
                         .order_by('?') \
                         .first()

    if not available_room:
        logger.debug("No room of type %s available. Product: %s",
                     room_type,
                     room_product)
    else:
        logger.debug("Found free room of type %s: %s",
                     room_type,
                     available_room.number)

    return available_room

def reconcile_orphan_rooms(guest_rows):
    # rooms may be orphaned due to placement changes, data corruption, machine elves
    def get_guest_obj(name):
        for guest in guest_rows:
            if name == f"{guest['first_name']} {guest['last_name']}":
                return guest

        return None

    orphan_rooms = Room.objects \
                       .filter(guest=None, is_available=False) \
                       .exclude(primary='')
    logger.debug("Attempting to reconcile %s orphan rooms", orphan_rooms.count())
    for room in orphan_rooms:
        guest = None
        # first check for a guest entry by sp_ticket_id
        try:
            if room.sp_ticket_id:
                guest = Guest.objects.get(ticket = room.sp_ticket_id)
                logger.info("Found guest %s by sp_ticket_id in DB for orphan room %s", guest.email, room.number)
        except Guest.DoesNotExist:
            pass

        if not guest:
            # then check for a guest entry by room number
            try:
                guest = Guest.objects.get(room_number = room.number)
                logger.info("Found guest %s by room_number in DB for orphan room %s", guest.email, room.number)
            except Guest.DoesNotExist:
                pass

        if not guest:
            # then check for a guest by name
            try:
                guest = Guest.objects.get(name = room.primary)
                logger.info("Found guest %s by name in DB for orphan room %s", guest.email, room.number)
            except Guest.DoesNotExist:
                pass

        if guest:
            # we found one, how lovely. associate room with it.
            room.guest = guest
            if room.primary != guest.name:
                logger.warning("names do not match for orphan room %s (%s, %s)",
                               room.number, room.primary, guest.name)
            elif room.primary == '':
                room.primary = guest.name

            room.save()
        else:
            # then check the guest list
            guest_obj = get_guest_obj(room.primary)
            if guest_obj:
                # we have one, that's nice
                logger.info("Found guest %s in CSV for orphan room %s",
                             guest_obj['email'], room.number)
                otp = phrasing()
                guest_update(guest_obj, otp, room)
                onboarding_email(guest_obj, otp)
            else:
                logger.warning("Unable to find guest %s for orphan room %s",
                               room.primary, room.number)

def guest_update(guest_dict, otp, room, og_guest=None):
    ticket_code = guest_dict['ticket_code']
    email = guest_dict['email']
    guest = None
    guest_changed = False
    try:
        # placed rooms may already have records
        # also sometimes people transfer rooms to themselves
        #   because why the frak not
        guest = Guest.objects.get(ticket=ticket_code,
                                  email=email)
        logger.debug("Found existing ticket %s for %s", ticket_code, email)
        if guest.room_number:
            if guest.room_number == room.number:
                logger.debug("Existing guest %s already associated with room %s",
                             email,
                             room.number)
            else:
                logger.warning("Existing guest %s not moving from %s to %s",
                               email,
                               guest.room_number,
                               room.number)
        else:
            logger.debug("Existing guest %s assigned to %s", email, room.number)
            guest.room_number = room.number
            guest_changed = True
    except Guest.DoesNotExist:
        # but most of the time the guest does not exist yet
        guest = Guest(name=f"{guest_dict['first_name']} {guest_dict['last_name']}",
                      ticket=guest_dict['ticket_code'],
                      jwt=otp,
                      email=email,
                      room_number=room.number)
        logger.debug("New guest %s in room %s", email, room.number)
        guest_changed = True

    # save guest (if needed) and then...
    if guest_changed:
        guest.save()

    # unassociated original owner (if present)
    if room.guest:
        if room.guest != og_guest:
            logger.warning("Unexpected original owner %s for room %s", room.guest.email, room.number)

        room.guest.room_number = None
        logger.debug("Removing original owner %s for room %s", room.guest.email, room.number)
        room.guest.save()

    # update room
    room.guest = guest
    room.is_available = False
    if room.primary != '' and room.primary != guest.name:
        logger.warning("Room %s already has a name set: %s!", room.number, room.primary)
    else:
        room.primary=guest.name

    room.save()

def create_guest_entries(guest_rows):
    retries = []
    for guest_obj in guest_rows:
        guest_entries = Guest.objects.filter(email=guest_obj["email"])
        trans_code = guest_obj['transferred_from_code']
        ticket_code = guest_obj['ticket_code']
        guest_name = f"{guest_obj['first_name']} {guest_obj['last_name']}"

        if trans_code == '' and guest_entries.count() == 0:
            # Unknown ticket, no transfer; new user
            otp = phrasing()
            room = find_room(guest_obj['product'])
            if not room:
                # sometimes this happens due to room transfers not being complete. hence the retry.
                logger.warning("No empty rooms available for %s", guest_obj['email'])
                retries.append(guest_obj)
                continue

            logger.info("Email doesnt exist: %s. Creating new guest contact.", guest_obj["email"])
            otp = phrasing()
            guest_update(guest_obj, otp, room)
            onboarding_email(guest_obj, otp)
        elif trans_code =='' and guest_entries.count() > 0:
            # There are a few cases that could pop up here
            # * admins / staff
            # * people share email addresses and soft-transfer rooms in sp
            if len([x.ticket for x in guest_entries if x.ticket == ticket_code]) == 0:
                room = find_room(guest_obj['product'])
                if not room:
                    logger.warning("No empty rooms available for %s", guest_entries[0].email)
                    retries.append(guest_obj)
                    continue

                logger.debug("assigning room %s to (unassigned ticket/room) %s", room.number, guest_entries[0].email)
                guest_update(guest_obj, guest_entries[0].jwt, room)
            else:
                logger.warning("Not sure how to handle non-transfer, existing user ticket %s", ticket_code)

        elif trans_code != "":
            # Transfered ticket...
            existing_guest = None
            logger.debug("Ticket %s is a transfer", trans_code)
            try:
                existing_guest = Guest.objects.get(ticket=trans_code)
            except Guest.DoesNotExist:
                # sometimes this happens due to transfers showing up earlier in the sp export than
                # the origial ticket. hence the retry.
                logger.warning("Ticket transfer (%s) but no previous guest found", trans_code)
                retries.append(guest_obj)
                continue

            existing_room = Room.objects.get(number = existing_guest.room_number)

            if guest_entries.count() == 0:
                # Transferring to new guest...
                logger.debug("Processing transfer %s (%s) from %s to (new guest) %s",
                             trans_code,
                             ticket_code,
                             existing_guest.email,
                             guest_obj['email'])
                otp = phrasing()
                guest_update(guest_obj, otp, existing_room, og_guest=existing_guest)
                onboarding_email(guest_obj, otp)
            else:
                # Transferring to existing guest...
                logger.debug("Processing transfer %s (%s) from %s to %s",
                             trans_code,
                             ticket_code,
                             existing_guest.email,
                             guest_obj['email'])
                # i think this will result in every jwt field being the same? guest entries
                # are kept around as part of transfers (ticket/email uniq) and when someone
                # has multiple rooms (email/room uniq)
                otp = guest_entries[0].jwt
                guest_update(guest_obj, otp, existing_room, og_guest=existing_guest)
        else:
            logger.warning("Not sure how to handle ticket %s", ticket_code)

    return retries



@api_view(['POST'])
def create_guests(request):
    guests_csv = "%s/guestUpload_latest.csv" % roombaht_config.TEMP_DIR
    if request.method == 'POST':
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

        _guest_fields, guest_rows = ingest_csv(guests_csv)
        # start by seeing if we can address orphaned placed rooms
        reconcile_orphan_rooms(guest_rows)
        # handle basic ingestion of guests
        retry_rows = create_guest_entries(guest_rows)
        if len(retry_rows) > 0:
            logger.debug("Retrying %s guest rows", len(retry_rows))
            # retry some guests bc secret party exports are non deterministic
            #  slash non ordered. this will include transfers for which the
            #  original ticket had not been yet entered and also (just in case)
            #  guests that saw rooms unavailable
            create_guest_entries(retry_rows)

        logger.info("guest list uploaded by %s", auth_obj['email'])
        return Response(str(json.dumps({"Creating guests using:": f'{guests_csv}'})),
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

        return Response(str(json.dumps({"admins": [admin.email for admin in admin_emails]})),
                        status=status.HTTP_201_CREATED)


@api_view(['POST'])
def request_metrics(request):
    if request.method == 'POST':
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

        rooooms = Room.objects.all()
        guest_unique = len(set([guest.email for guest in Guest.objects.all()]))
        guest_count = Guest.objects.all().count()
        rooms_count = rooooms.count()
        rooms_occupied = rooooms.exclude(is_available=True).count()
        rooms_swappable = rooooms.exclude(is_swappable=False).count()
        resp = str(json.dumps({"guest_count": guest_count,
                               "rooms_count": rooms_count,
                               "rooms_occupied": rooms_occupied,
                               "guest_unique": guest_unique,
                               "rooms_swappable": rooms_swappable
                               }))
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
