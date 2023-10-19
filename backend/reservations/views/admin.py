
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
from reservations.helpers import ingest_csv, phrasing, egest_csv
from reservations.constants import ROOM_LIST

logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

logger = logging.getLogger('ViewLogger_admin')

RANDOM_ROOMS = os.environ.get('RANDOM_ROOMS', True)

def assign_room(type_purchased_secpty):
    for roomtype in ROOM_LIST.items():
        if(type_purchased_secpty in roomtype[1]):
            set_room = roomtype[0]
            break
        else:
            set_room = "Room type not found"


    if(RANDOM_ROOMS=="TRUE"):
        no_guest = Room.objects.filter(guest=None, is_available=True)
        for room in no_guest:
            if(room.name_take3 == set_room):
                logger.info(f"[+] Assigned room number: {room.number}")
                return room
            else:
                pass
        logger.warn(f'[-] No room of matching type available. looking for: {type_purchased_secpty} ')
        return None
    else:
        # testing purposes
        logger.warning(f'test room assigned in create')
        return Room(number=666)


def guest_contact_new(guest_new, otp, email_onboarding=False, room=None):
    ''' Create guest send email '''
    logger.info(f"[+] Creating guest: {guest_new['first_name']} {guest_new['last_name']}, {guest_new['email']}, {guest_new['ticket_code']}")
    existing_ticket = Guest.objects.filter(ticket=guest_new["ticket_code"])
    # verify ticket does not exist
    if(len(existing_ticket)!=0):
        return
    if(room is None):
        room = assign_room(guest_new["product"])
    if(room is None):
        logging.debug("[-] Out of empty rooms")
        return

    guest=Guest(name=guest_new['first_name']+" "+guest_new['last_name'],
        email=guest_new['email'],
        ticket=guest_new['ticket_code'],
        jwt=otp,
        room_number=room.number)
    guest.save()

    room.guest=guest
    room.is_available = False
    if room.primary != '':
        logger.warning("room %s alraedy has a name set: %s" % (room.number, room.primary))
    else:
        room.primary=guest.name

    room.save()

    logger.info(f"[+] Assigned room number: {room.number}")
    if(email_onboarding):
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
                http://rooms.take3presents.com/login

                Good Luck, Starfighter.

            """

            send_mail("RoomService RoomBaht",
                      body_text,
                      "placement@take3presents.com",
                      [guest_new["email"]],
                      auth_user="placement@take3presents.com",
                      auth_password=apppass,
                      fail_silently=False,)


def create_guest_entries(guest_file):
    _guest_fields, guest_rows = ingest_csv(guest_file)

    for guest_new in guest_rows:
        if(guest_new['product'][:3] == "Art"):
            continue

        if ("Hard Rock" in guest_new["product"]):
            continue

        guest_entries = Guest.objects.filter(email=guest_new["email"])
        trans_code = guest_new['transferred_from_code']
        tix_exist = [guest.ticket for guest in guest_entries if guest.ticket==guest_new['ticket_code']]

        # Create with email
        if(len(guest_entries)==0):
            logger.info(f'Email doesnt exist: {guest_new["email"]} ql: {guest_entries}. Creating new guest contact.')
            guest_contact_new(guest_new, phrasing(), email_onboarding=True)
        # Update from ticket transfer
        elif(trans_code!=""):
            try:
                existing_guest = Guest.objects.filter(ticket=trans_code)[0]
            except IndexError as e:
                logger.warn(f'[-] Ticket transfer but no previous ticket id found')
                continue
            existing_room = Room.objects.get(number = existing_guest.room_number)
            logger.info(f'Ticket is a transfer. ')
            otp = phrasing()
            if(len(guest_entries)==0):
                guest_contact_new(guest_new, otp, email_onboarding=True, room=existing_room)
            else:
                guest_contact_new(guest_new, otp, email_onboarding=False, room=existing_room)
            existing_guest.delete()
        # Create without email
        else:
            if(len(tix_exist)==0):
                logger.info(f'Email exists. Creating new ticket.')
                guest_contact_new(guest_new, phrasing(), email_onboarding=False)


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

        create_guest_entries(guests_csv)

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

        logger.debug(f'guest upload: {data["guest_list"]}')
        rows = data['guest_list'].split('\n')

        new_guests = []
        guest_fields, guests = ingest_csv(rows)

        if 'ticket_code' not in guest_fields or \
           'ticket_status' not in guest_fields or \
           'product' not in guest_fields:
            return Response("Unknown file", status=status.HTTP_400_BAD_REQUEST)

        room_products = []
        for _take3_product, hotel_products in ROOM_LIST.items():
            for product in hotel_products:
                room_products.append(product)

        for guest in guests:
            if guest['product'] not in room_products:
                logger.debug("Ticket %s has product we don't care about: %s",
                             guest['ticket_code'],
                             guest['product'])
                continue

            existing_ticket = None
            try:
                existing_ticket = Guest.objects.get(ticket=guest['ticket_code'])
            except Guest.DoesNotExist:
                pass

            if existing_ticket:
                logger.warning("[-] Ticket %s from upload already in db", guest['ticket_code'])
                continue

            new_guests.append(guest)

        egest_csv(new_guests,
                  guest_fields,
                  "%s/guestUpload_latest.csv" % os.environ['ROOMBAHT_TMP'])

        resp = str(json.dumps({"received_guests": len(guests),
                               "new_guests": len(new_guests),
                               "diff": diff_latest(new_guests),
                               "headers": guest_fields,
                               "first_row": new_guests[0],
                               "status": "Ready to Load..."
                               }))

        return Response(resp, status=status.HTTP_201_CREATED)
