
import os
import time
import logging
import jwt
import datetime
import json
import string
import random
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
from .rooms import validate_jwt
from ..reporting import dump_guest_rooms, diff_latest
from reservations.helpers import ingest_csv, phrasing, egest_csv, my_url
from reservations.constants import ROOM_LIST

logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

logger = logging.getLogger('ViewLogger_admin')

RANDOM_ROOMS = os.environ.get('RANDOM_ROOMS', True)

def onboarding_email(guest_new, otp):
    hostname = my_url()
    if os.environ.get('ROOMBAHT_SEND_MAIL', 'FALSE').lower() == 'true':
        time.sleep(5)
        apppass = os.environ['ROOMBAHT_EMAIL_HOST_PASSWORD']
        logger.debug(f'[+] Sending invite for guest {guest_new["first_name"]} {guest_new["last_name"]}')

        body_text = f"""
        BleepBloopBleep, this is the Room Service RoomBaht for Room Swaps letting you know the floors have been cleaned and you have been assigned a room. No bucket or mop needed.

        After you login below you can view your current room, look at other rooms and send trade requests. This functionality is only available until Monday 11/7 at 5pm PST, so please make sure you are good with what you have or trade early.

        Goes without saying, but don't forward this email.

        This is your password, there are many like it but this one is yours. Once you use this password on a device, RoomBaht will remember you, but only on that device.
        Copy and paste this password. Because let’s face it, no one should trust humans to make passwords:
        {otp}
        {my_url}/login

        Good Luck, Starfighter.

        """

        send_mail("RoomService RoomBaht",
                  body_text,
                  os.environ['ROOMBAHT_EMAIL_HOST_USER'],
                  [guest_new["email"]],
                  auth_user=os.environ['ROOMBAHT_EMAIL_HOST_USER'],
                  auth_password=os.environ['EMAIL_HOST_PASSWORD'],
                  fail_silently=False)

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
        # first check for a guest entry by room number
        guest = None
        try:
            guest = Guest.objects.get(room_number = room.number)
        except Guest.DoesNotExist:
            pass

        # then check for a guest by name
        try:
            guest = Guest.objects.get(name = room.primary)
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

            logger.debug("Found guest %s in DB for orphan room %s", guest.email, room.number)
            room.save()
        else:
            # then check the guest list
            guest_obj = get_guest_obj(room.primary)
            if guest_obj:
                # we have one, that's nice
                logger.debug("Found guest %s in CSV for orphan room %s",
                             guest_obj['email'], room.number)
                otp = phrasing()
                guest_update(guest_obj, otp, room)
                onboarding_email(guest_obj, otp)
            else:
                logger.warning("Unable to find guest %s for orphan room %s",
                               room.primary, room.number)

def guest_remove(guest):
    guest_rooms = Room.objects.filter(guest=guest)
    if guest_rooms.count() > 0:
        raise Exception("Not removing guest %s as it would orphan rooms %s" % \
                        ( guest.email, ','.join([x.number for x in guest_rooms])))

    guest.delete()
    logger.debug("Removed guest %s, ticket %s", guest.email, guest.ticket)

def guest_update(guest_dict, otp, room):
    # define our new guest object
    guest = Guest(name=f"{guest_dict['first_name']} {guest_dict['last_name']}",
                  ticket=guest_dict['ticket_code'],
                  jwt=otp,
                  email=guest_dict['email'],
                  room_number=room.number)

    existing_ticket = None
    try:
        existing_ticket = Guest.objects.get(ticket=guest.ticket)
    except Guest.DoesNotExist:
        pass

    if existing_ticket:
        logger.warning("Ticket %s already exists when creating user %s",
                       guest.ticket,
                       guest.email)
        return

    # save guest and then...
    guest.save()
    # update room
    room.guest = guest
    room.is_available = False
    if room.primary != '' and room.primary != guest.name:
        logger.warning("Room %s already has a name set: %s!", room.number, room.primary)
    else:
        room.primary=guest.name

    room.save()
    logger.info("New ticket %s - %s in %s",
                guest.ticket,
                guest.email,
                guest.room_number)

def create_guest_entries(guest_rows):
    for guest_obj in guest_rows:
        guest_entries = Guest.objects.filter(email=guest_obj["email"])
        trans_code = guest_obj['transferred_from_code']
        ticket_code = guest_obj['ticket_code']

        if trans_code == '' and guest_entries.count() == 0:
            # Unknown ticket, no transfer; new user
            otp = phrasing()
            room = find_room(guest_obj['product'])
            if not room:
                logger.warning("No empty rooms available for %s", guest_obj['email'])
                continue

            logger.info("Email doesnt exist: %s. Creating new guest contact.", guest_obj["email"])
            otp = phrasing()
            guest_update(guest_obj, otp, room)
            onboarding_email(guest_obj, otp)
        elif trans_code != "":
            # Transfered ticket...
            existing_guest = None
            logger.debug("Ticket %s is a transfer", trans_code)
            try:
                existing_guest = Guest.objects.get(ticket=trans_code)
            except Guest.DoesNotExist:
                logger.warning("Ticket transfer (%s) but no previous guest found!", trans_code)
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
                guest_update(guest_obj, otp, existing_room)
                onboarding_email(guest_obj, otp)
            else:
                # Transferring to existing guest...
                logger.debug("Processing transfer %s (%s) from %s to %s",
                             trans_code,
                             ticket_code,
                             existing_guest.email,
                             guest_obj['email'])
                guest_update(guest_obj, guest_entries[0].jwt, existing_room)

            guest_remove(existing_guest)


def validate_admin(data):
    try:
        jwt_data=data["jwt"]
    except KeyError as e:
        logger.info(f"[-] Missing fields {request.data}")
        return False
    email = validate_jwt(jwt_data)

    if (email is None):
        logger.info(f"[-] No guest with that email")
        return False
    staff = Staff.objects.filter(email=email)

    if(len(staff)==0 or staff[0].is_admin!=True):
        logger.info(f"[-] No admin by that email")
        return False
    else:
        return True


@api_view(['POST'])
def create_guests(request):
    guests_csv = "%s/guestUpload_latest.csv" % os.environ['ROOMBAHT_TMP']
    if request.method == 'POST':
        data = request.data["data"]
        if not validate_admin(data):
            return Response("User not admin", status=status.HTTP_400_BAD_REQUEST)

        _guest_fields, guest_rows = ingest_csv(guests_csv)
        reconcile_orphan_rooms(guest_rows)
        create_guest_entries(guest_rows)

        return Response(str(json.dumps({"Creating guests using:": f'{guests_csv}'})),
                                             status=status.HTTP_201_CREATED)


@api_view(['POST'])
def run_reports(request):
    if request.method == 'POST':
        data = request.data["data"]
        logger.info(f'Run reports attempt')
        if(validate_admin(data)==True):
            admin_emails = Staff.objects.filter(is_admin=True)
            guest_dump_file, room_dump_file = dump_guest_rooms()
            if os.environ.get('ROOMBAHT_SEND_MAIL', 'FALSE').lower() == 'true':
                logger.info(f'sending admin emails: {admin_emails}')
                conn = get_connection()
                msg = EmailMessage(subject="RoomBaht Report",
                                   body="Diff dump, guest dump, room dump",
                                   to=[admin.email for admin in admin_emails],
                                   connection=conn)
                #TODO(tb) verify these files
                msg.attach_file(guest_dump_file)
                msg.attach_file(room_dump_file)
                if os.path.exists("%s/diff_latest.csv" % os.environ['ROOMBAHT_TMP']):
                    msg.attach_file("%s/diff_latest.csv" % os.environ['ROOMBAHT_TMP'])

                if os.path.exists("%s/guestUpload_latest.csv" % os.environ['ROOMBAHT_TMP']):
                    msg.attach_file("%s/guestUpload_latest.csv" % os.environ['ROOMBAHT_TMP'])

                msg.send()
            return Response(str(json.dumps({"admins": [admin.email for admin in admin_emails]})),
                                           status=status.HTTP_201_CREATED)
        else:
            return Response("User not admin", status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def request_metrics(request):
    if request.method == 'POST':
        data = request.data["data"]
        if(validate_admin(data)==True):
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
        else:
            return Response("User not admin", status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def guest_file_upload(request):
    if request.method == 'POST':
        data = request.data["guest"]
        if not validate_admin(data):
            return Response("User not admin", status=status.HTTP_400_BAD_REQUEST)

        rows = data['guest_list'].split('\n')
        new_guests = []
        guest_fields, guests = ingest_csv(rows)

        # basic input validation, make sure it's the right csv
        if 'ticket_code' not in guest_fields or \
           'ticket_status' not in guest_fields or \
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
                  "%s/guestUpload_latest.csv" % os.environ['ROOMBAHT_TMP'])

        resp = str(json.dumps({"received_rows": len(guests),
                               "valid_rows": len(new_guests),
                               "diff": diff_latest(new_guests),
                               "headers": guest_fields,
                               "first_row": new_guests[0],
                               "status": "Ready to Load..."
                               }))

        return Response(resp, status=status.HTTP_201_CREATED)
