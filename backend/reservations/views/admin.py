
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

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger('ViewLogger_admin')

class RoomCounts:
    counts = {}
    def __init__(self):
        for room_type in ROOM_LIST.keys():
            self.counts[room_type] = {
                'available': Room.objects.filter(name_take3=room_type, is_available=True).count(),
                'allocated': 0,
                'shortage': 0,
                'orphan': 0,
                'transfer': 0
            }
    def shortage(self, product):
        self.counts[product]['shortage'] += 1

    def allocated(self, product):
        self.counts[product]['allocated'] += 1

    def orphan(self, product):
        self.counts[product]['orphan'] += 1

    def transfer(self, product):
        self.counts[product]['transfer'] += 1

    def output(self):
        lines = []
        for room_type, counts in self.counts.items():
            if counts['orphan'] > 0:
                logger.info("Reunited %s %s orphans", counts['orphan'], room_type)

            if counts['shortage'] > 0:
                logger.warning("%s room short inventory by %s! available:%s, allocated:%s, transfer: %s, orphan: %s",
                               room_type,
                               counts['shortage'],
                               counts['available'],
                               counts['allocated'],
                               counts['transfer'],
                               counts['orphan'])
            remaining = Room.objects.filter(name_take3=room_type, is_available=True).count()

            line = f"{room_type} room allocated: {counts['allocated']}, transfer: {counts['transfer']}, remaining: {remaining}, orphan: {counts['orphan']} (of {counts['available']} available)"
            logger.info(line)
            lines.append(line)

        return lines

def short_product_code(product):
    for a_room, a_product in ROOM_LIST.items():
        if product in a_product:
            return a_room

    if product in ROOM_LIST.keys():
        return product

    raise Exception('Should never not find a short product code tho')

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

def find_room(guest, room_counts, assign_rooms=False, hotel="Ballys"):
    room_type = short_product_code(guest["product"])

    if not room_type:
        raise Exception("Unable to actually find room type for %s" % guest["product"])

    # We only auto-assign rooms if these criteria are met
    #  * must be available
    #  * must not be art - we should rarely see these as art rooms are almost always placed
    if(assign_rooms==True):
        available_room = Room.objects.filter(is_available=True,
                                             is_art=False,
                                             name_take3=room_type,
                                            ).order_by('?') .first()
    else:
        return Room(name_take3="NullRoom",
                    name_hotel=hotel,
                    number=666
                    )
    if not available_room:
        logger.debug("No room of type %s available. Product: %s",
                     room_type,
                     guest["product"])
        logger.warning("No empty rooms available for %s", guest['email'])
        room_counts.shortage(short_product_code(guest['product']))
        return None
    else:
        logger.debug("Found free room of type %s: %s",
                     room_type,
                     available_room.number)

    return available_room

def transfer_chain(ticket, guest_rows, depth=1):
    chain = []
    for row in guest_rows:
        if ticket == row['ticket_code']:
            chain.append(row)
            if row['transferred_from_code'] != '':
                a_chain = transfer_chain(row['transferred_from_code'],
                                         guest_rows,
                                         depth + 1)
                if len(a_chain) == 0:
                    logger.debug("Unable to find recursive ticket for %s (depth %s)",
                                 ticket, depth)
                    return chain

                chain += a_chain

            logger.debug("Found transfer ticket %s source (depth %s)", ticket, depth)

    return chain

def reconcile_orphan_rooms(guest_rows, room_counts):
    # rooms may be orphaned due to placement changes, data corruption, machine elves
    orphan_tickets = []
    def get_guest_obj(field, value):
        for guest in guest_rows:
            if field == 'name' and value == f"{guest['first_name']} {guest['last_name']}":
                return guest

            if field == 'ticket' and value == guest['ticket_code']:
                return guest

        return None

    orphan_rooms = Room.objects \
                       .filter(guest=None, is_available=False) \
                       .exclude(primary='')
    logger.debug("Attempting to reconcile %s orphan rooms", orphan_rooms.count())
    for room in orphan_rooms:
        guest = None
        # some validation
        if room.sp_ticket_id and room.is_comp:
            logger.warning("Room %s is comp'd and has ticket %s; skipping",
                           room.number, room.sp_ticket_id)
        # first check for a guest entry by sp_ticket_id
        try:
            if room.sp_ticket_id:
                guest = Guest.objects.get(ticket = room.sp_ticket_id)
                logger.info("Found guest %s by sp_ticket_id in DB for orphan %s room %s",
                            guest.email, room.name_take3, room.number)
        except Guest.DoesNotExist:
            pass

        if not guest:
            # then check for a guest entry by room number
            try:
                guest = Guest.objects.get(room_number = room.number)
                logger.info("Found guest %s by room_number in DB for orphan %s room %s",
                            guest.email, room.name_take3, room.number)
            except Guest.DoesNotExist:
                pass

        if guest:
            # we found one, how lovely. associate room with it.
            room.guest = guest
            if room.primary != guest.name:
                logger.warning("names do not match for orphan room %s (%s, %s, %s fuzziness)",
                               room.number, room.primary, guest.name,
                               fuzz.ratio(room.primary, guest.name))
                continue

            if room.primary == '':
                room.primary = guest.name

            room_counts.orphan(room.name_take3)
            room.save()
        else:
            # then check the guest list
            guest_obj = None
            if room.sp_ticket_id is not None:
                guest_obj = get_guest_obj('ticket', room.sp_ticket_id)
                if guest_obj:
                    logger.info("Found guest %s by ticket %s in CSV for orphan %s room %s",
                                guest_obj['email'],
                                room.sp_ticket_id,
                                room.name_take3,
                                room.number)
                    # if this is a transfer, need to account for those as well
                    if guest_obj['transferred_from_code'] != '':
                        chain = transfer_chain(guest_obj['transferred_from_code'], guest_rows)
                        if len(chain) > 0:
                            for chain_guest in chain:
                                # add stubs to represent the transfers
                                stub = Guest(name=f"{chain_guest['first_name']} {chain_guest['last_name']}".title(),
                                             email=chain_guest['email'],
                                             ticket=chain_guest['ticket_code'])
                                stub.save()
                                orphan_tickets.append(chain_guest['ticket_code'])


            if guest_obj:
                # we have one, that's nice
                otp = phrasing()
                guest_update(guest_obj, otp, room, room_counts)
                onboarding_email(guest_obj, otp)
            else:
                if room.is_comp:
                    logger.debug("Ignoring comp'd %s room %s, guest %s",
                                 room.name_take3, room.number, room.primary)
                else:
                    logger.warning("Unable to find guest %s for (non-comp) orphan room %s",
                                   room.primary, room.number)

                    possibilities = [x for x in process.extract(room.primary, [f"{x['first_name']} {x['last_name']}" for x in guest_rows]) if x[1] > 85]
                    if len(possibilities) > 0:
                        logger.warning("Found %s fuzzy name possibilities in CSV for %s in orphan room %s: %s",
                                       len(possibilities),
                                       room.primary,
                                       room.number,
                                       ','.join([f"{x[0]}:{x[1]}" for x in possibilities]))


                continue

        if room.sp_ticket_id:
            orphan_tickets.append(room.sp_ticket_id)

    return orphan_tickets

def guest_update(guest_dict, otp, room, room_counts, og_guest=None):
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
                logger.debug("Existing guest %s already associated with room %s (%s)",
                             email,
                             room.number,
                             room.name_tak3)
            else:
                # transfers for placed users
                logger.warning("Existing guest %s not moving from %s to %s (%s)",
                               email,
                               guest.room_number,
                               room.number,
                               room.name_take3)

            return

        logger.debug("Existing guest %s assigned to %s (%s)",
                     email, room.number, room.name_take3)
        guest.room_number = room.number
        guest_changed = True

    except Guest.DoesNotExist:
        # but most of the time the guest does not exist yet
        guest = Guest(name=f"{guest_dict['first_name']} {guest_dict['last_name']}".title(),
                      ticket=guest_dict['ticket_code'],
                      jwt=otp,
                      email=email,
                      room_number=room.number)
        logger.debug("New guest %s in room %s (%s)",
                     email, room.number, room.name_take3)
        guest_changed = True

    # save guest (if needed) and then...
    if guest_changed:
        guest.save()

    if room.primary != '' and room.primary != guest.name:
        logger.warning("Room %s already has a name set: %s, guest %s!",
                       room.number, room.primary, guest.name)

    # unassociated original owner (if present)
    if room.guest and og_guest:
        if room.guest != og_guest:
            logger.warning("Unexpected original owner %s for room %s", room.guest.email, room.number)

        room.guest.room_number = None
        logger.debug("Removing original owner %s for room %s", room.guest.email, room.number)
        room.guest.save()

    # update room
    room.guest = guest
    room.is_available = False

    room.primary=guest.name
    room.save()

def deal_with_transfers(room_count, guest, trans_code, guest_rows, guest_entries, room_counts, transferred_tickets):
    # Transfered ticket...
    existing_guest = None
    ticket_code = guest['ticket_code']
    try:
        existing_guest = Guest.objects.get(ticket=trans_code)
        logger.info(f'esisting guest found: {existing_guest.room_number}')
    except Guest.DoesNotExist:
        # sometimes this happens due to transfers showing up earlier in the sp export than
        # the origial ticket. so we go through the full set of rows
        chain = transfer_chain(trans_code, guest_rows)
        if len(chain) == 0:
            logger.warning("Ticket transfer (%s) but no previous guest found", trans_code)
            return

        for chain_guest in chain:
            # add stub guests
            stub = Guest(name=f"{chain_guest['first_name']} {chain_guest['last_name']}".title(),
                         email=chain_guest['email'],
                         ticket=chain_guest['ticket_code'])
            stub.save()

            transferred_tickets.append(chain_guest['ticket_code'])

        room = find_room(guest, room_counts)

        email_chain = ','.join([x['email'] for x in chain])
        if guest_entries.count() == 0:
            logger.debug("Processing transfer %s (%s) from %s to (new guest) %s",
                         trans_code,
                         ticket_code,
                         email_chain,
                         guest['email'])
            otp = phrasing()
            guest_update(guest, otp, room, room_counts)
        else:
            logger.debug("Processing transfer %s (%s) from %s to %s",
                         trans_code,
                         ticket_code,
                         email_chain,
                         guest['email'])
            otp = guest_entries[0].jwt
            guest_update(guest, otp, room, room_counts)

        room_counts.transfer(room.name_take3)

        return

    if(existing_guest.room_number!=None):
        existing_room = Room.objects.get(number = existing_guest.room_number)
    else:
        return

    if guest_entries.count() == 0:
        # Transferring to new guest...
        logger.debug("Processing placed transfer %s (%s) from %s to (new guest) %s",
                     trans_code,
                     ticket_code,
                     existing_guest.email,
                     guest['email'])
        otp = phrasing()
        guest_update(guest, otp, existing_room, room_counts, og_guest=existing_guest)
        onboarding_email(guest, otp)
    else:
        # Transferring to existing guest...
        logger.debug("Processing placed transfer %s (%s) from %s to %s",
                     trans_code,
                     ticket_code,
                     existing_guest.email,
                     guest['email'])
        # i think this will result in every jwt field being the same? guest entries
        # are kept around as part of transfers (ticket/email uniq) and when someone
        # has multiple rooms (email/room uniq)
        otp = guest_entries[0].jwt
        guest_update(guest, otp, existing_room, room_counts, og_guest=existing_guest)

    room_counts.transfer(existing_room.name_take3)


def create_guest_entries(guest_rows, room_counts, orphan_tickets=[]):
    transferred_tickets = []

    for guest_obj in guest_rows:
        guest_entries = Guest.objects.filter(email=guest_obj["email"])
        trans_code = guest_obj['transferred_from_code']
        ticket_code = guest_obj['ticket_code']

        if ticket_code in transferred_tickets:
            logger.debug("Skipping transferred ticket %s", ticket_code)
            continue

        if ticket_code in orphan_tickets:
            logger.debug("Skipping ticket %s from orphan processing", ticket_code)
            continue

        if ticket_code in roombaht_config.IGNORE_TRANSACTIONS:
            logger.info("Skipping ticket %s as it is on our ignore list", ticket_code)
            continue

        if trans_code == '' and guest_entries.count() == 0:
            # Unknown ticket, no transfer; new user
            room = find_room(guest_obj, room_counts)
            if not room:
                # sometimes this happens due to room transfers not being complete.
                logger.warning("No empty rooms available for %s", guest_obj['email'])
                room_counts.shortage(short_product_code(guest_obj['product']))
                continue

            logger.info("Email doesnt exist: %s. Creating new guest contact.", guest_obj["email"])
            otp = phrasing()
            guest_update(guest_obj, otp, room, room_counts)
            onboarding_email(guest_obj, otp)
            room_counts.allocated(room.name_take3)
        elif trans_code =='' and guest_entries.count() > 0:
            # There are a few cases that could pop up here
            # * admins / staff
            # * people share email addresses and soft-transfer rooms in sp
            if len([x.ticket for x in guest_entries if x.ticket == ticket_code]) == 0:
                room = find_room(guest_obj, room_counts)
                if not room:
                    logger.warning("No empty rooms available for %s", guest_entries[0].email)
                    room_counts.shortage(short_product_code(guest_obj['product']))
                    continue

                logger.debug("assigning room %s to (unassigned ticket/room) %s", room.number, guest_entries[0].email)
                guest_update(guest_obj, guest_entries[0].jwt, room, room_counts)
                room_counts.allocated(room.name_take3)
            else:
                logger.warning("Not sure how to handle non-transfer, existing user ticket %s", ticket_code)

        elif trans_code != "":
            deal_with_transfers(room_counts, guest_obj, trans_code, guest_rows, guest_entries, room_counts, transferred_tickets)

        else:
            logger.warning("Not sure how to handle ticket %s", ticket_code)


@api_view(['POST'])
def create_guests(request):
    guests_csv = "%s/guestUpload_latest.csv" % roombaht_config.TEMP_DIR
    if request.method == 'POST':
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

        _guest_fields, guest_rows = ingest_csv(guests_csv)
        # actually keep some metrics here
        room_counts = RoomCounts()
        # start by seeing if we can address orphaned placed rooms
        orphan_tickets = reconcile_orphan_rooms(guest_rows, room_counts)
        # handle basic ingestion of guests
        create_guest_entries(guest_rows, room_counts, orphan_tickets)

        lines = room_counts.output()
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
