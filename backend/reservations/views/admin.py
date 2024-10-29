
import os
import time
import logging
import jwt
import datetime
import json
import re
import string
import sys

from random import randint
from csv import DictReader, DictWriter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import status
from django.core.mail import send_mail, EmailMessage, get_connection
from fuzzywuzzy import process, fuzz
from ..models import Staff
from ..models import Guest
from ..models import Room
from ..models import UnknownProductError
from .rooms import phrasing
from ..reporting import (diff_latest, dump_guest_rooms, swaps_report,
                         hotel_export, diff_swaps_count, rooming_list_export)
from reservations.helpers import ingest_csv, phrasing, egest_csv, my_url, send_email
from reservations.constants import ROOM_LIST
import reservations.config as roombaht_config
from reservations.auth import authenticate_admin, unauthenticated
from reservations.ingest_models import SecretPartyGuestIngest

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger('ViewLogger_admin')

class RoomMeta:
    counts = {}
    msgs = []
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

    def warning(self, msg):
        logger.warning(msg)
        self.msgs.append(f"[warning] {msg}")

    def error(self, msg):
        logger.error(msg)
        self.msgs.append(f"[ERRAR] {msg}")

    def output(self):
        lines = []
        for room_type, counts in self.counts.items():
            if counts['orphan'] > 0:
                logger.info("Reunited %s %s orphans", counts['orphan'], room_type)


            remaining = Room.objects.filter(name_take3=room_type, is_available=True).count()
            line = f"{room_type} shortage: {counts['shortage']} allocated: {counts['allocated']}, transfer: {counts['transfer']}, remaining: {remaining}, orphan: {counts['orphan']} (of {counts['available']} available)"
            if counts['shortage'] > 0:
                logger.warning("%s room short inventory by %s! available:%s, allocated:%s, transfer: %s, orphan: %s",
                               room_type,
                               counts['shortage'],
                               counts['available'],
                               counts['allocated'],
                               counts['transfer'],
                               counts['orphan'])
                lines.append(f"warning: {line}")
            else:
                if counts['allocated'] > 0:
                    lines.append(f"info: {line}")

                logger.info(line)

        return lines + self.msgs

def find_room(room_product):
    room_type = Room.short_product_code(room_product)
    hotel = Room.derive_hotel(room_product)
    if not room_type:
        raise Exception("Unable to actually find room type for %s" % room_product)

    # We only auto-assign rooms if these criteria are met
    #  * must be available
    #  * must not be art - we should rarely see these as art rooms are almost always placed
    available_room = Room.objects \
                         .filter(is_available=True,
                                 name_take3=room_type,
                                 name_hotel=hotel
                                 ) \
                         .order_by('?') \
                         .first()

    if not available_room:
        logger.debug("No room of type %s available in %s. Product: %s",
                     room_type,
                     hotel,
                     room_product)
    else:
        logger.debug("Found free room of type %s in %s: %s",
                     room_type,
                     hotel,
                     available_room.number)

    return available_room

def transfer_chain(ticket, guest_rows, depth=1):
    chain = []
    for row in guest_rows:
        if ticket == row.ticket_code:
            chain.append(row)
            if row.transferred_from_code != '':
                a_chain = transfer_chain(row.transferred_from_code,
                                         guest_rows,
                                         depth + 1)
                if len(a_chain) == 0:
                    logger.debug("Unable to find recursive ticket for %s (depth %s)",
                                 ticket, depth)
                    return chain

                chain += a_chain

            logger.debug("Found transfer ticket %s source (depth %s)", ticket, depth)

    return chain

def reconcile_orphan_chain(guest_obj, guest_rows):
    orphan_tickets = []
    chain = transfer_chain(guest_obj.transferred_from_code, guest_rows)
    for chain_guest in chain:
        chain_name = f"{chain_guest.first_name} {chain_guest.last_name}".title()
        stub = None
        # ensure stub exists and matches reality
        try:
            stub = Guest.objects.get(email=chain_guest.email,
                                     ticket=chain_guest.ticket_code)
            if chain_guest.transferred_from_code and \
               stub.transfer != chain_guest.transferred_from_code:
                raise Exception(f"unexpected mismatched sp transfer {chain_guest.ticket_code} "
                                f"{chain_guest.transferred_from_code} -> {stub.transfer}")

        except Guest.DoesNotExist:
            # add stubs to represent the transfers
            #   * note these still get a pw given our auth model is tied
            #     to our guest model
            stub = Guest(name=chain_name,
                         email=chain_guest.email,
                         ticket=chain_guest.ticket_code,
                         jwt=phrasing())
            logger.debug("Created stub guest %s with ticket %s",
                         chain_guest.email, chain_guest.ticket_code)
            if chain_guest.transferred_from_code:
                stub.transfer = chain_guest.transferred_from_code

            stub.save()

        # mark this part of the transfer chain as already processed
        orphan_tickets.append(chain_guest.ticket_code)

    return orphan_tickets

def reconcile_orphan_rooms(guest_rows, room_meta):
    """
    rooms in the database may be orphaned due to the following reasons, in
    order of likelyhood of occuing
      * non-comp'd placed rooms
      * shuffling around of non-comp'd placed rooms
      * data corruption
      * non deterministic sp exports when resolving transfer chains
      * machine elves

    orphaned rooms manifest as having no associated guest record and
    showing as non-available i.e. already has someone, placed
    or otherwise within the room.
    """
    def get_guest_obj(field, value):
        """
        helper function for retrieving guest object from ingested csv
        """
        for guest in guest_rows:
            if field == 'name' and value == f"{guest.first_name} {guest.last_name}":
                return guest

            if field == 'ticket' and value == guest.ticket_code:
                return guest

        return None

    orphan_tickets = []
    orphan_rooms = Room.objects \
                       .filter(guest=None,
                               is_available=False) \
                       .exclude(names__isnull=True)
    logger.debug("Attempting to reconcile %s orphan rooms", orphan_rooms.count())
    for room in orphan_rooms:
        # if the room is placed and has no sp ticket id then ain't nothing to do
        if room.is_placed and room.sp_ticket_id == '':
            continue

        guest = None
        # first check for a guest entry by sp_ticket_id
        try:
            if room.sp_ticket_id:
                guest = Guest.objects.get(ticket = room.sp_ticket_id)
                logger.info("Found guest %s by sp_ticket_id in DB for orphan %s %s room %s",
                            guest.email, room.name_take3, room.name_hotel, room.number)
        except Guest.DoesNotExist:
            pass

        if guest:
            # we found one, how lovely
            #   * associate room with this guest record
            #   * ensure the owner is listed as a room occupant
            if not room.guest:
                room.guest = guest
            elif room.guest and room.guest != guest:
                logger.info("marking orphan room %s %s as transferred %s -> %s",
                            room.name_hotel, room.number, room.guest.name, guest.name)
                if room.resident(guest):
                    room_meta.warning(f"removing old owner {room.guest.name} of orphan room {room.name_hotel}"
                                      f" {room.number} from list of room occupants {room.names}")
                    room.resident_remove(guest.name)

            if not room.resident(guest):
                room_meta.warning(f"owner of orphan room {room.name_hotel} {room.number}"
                                  f" {guest.name} is not in list of room occupants {room.names}")
                room.resident_add(guest.name)

            room_meta.orphan(room.name_take3)
            if room.is_dirty(check_relationship=True):
                room.save()
        else:
            # run through the rest of the sp export as it is not always in a
            # consistent order and we may need to handle transfer chains
            guest_obj = None
            if room.sp_ticket_id is not None:
                # try and find guest record from ticket id associated with orphan room
                guest_obj = get_guest_obj('ticket', room.sp_ticket_id)
                if guest_obj:
                    logger.debug("Found guest %s by ticket %s in CSV for orphan %s room %s %s",
                                 guest_obj.email,
                                 room.sp_ticket_id,
                                 room.name_take3,
                                 room.name_hotel,
                                 room.number)
                    # if this is a transfer, need to ensure every guest in transfer chain
                    # exists as (at least) a stub entry
                    if guest_obj.transferred_from_code != '':
                        chain_tickets = reconcile_orphan_chain(guest_obj, guest_rows)
                        orphan_tickets = orphan_tickets + chain_tickets

            if guest_obj:
                # we have one, that's nice. make sure to use the same otp
                # if we can for this guest
                existing_guests = Guest.objects.filter(email=guest_obj.email)
                otp = phrasing()
                if len(existing_guests) > 0:
                    otp = existing_guests[0].jwt

                guest_update(guest_obj, otp, room)
            else:
                # this should only happen for "placeholder" rooms w/o actual names..
                room_meta.warning(f"Unable to reconcile guest records for orphan room {room.name_hotel} {room.number}")
                # ... and we will try again later...
                continue

        # mark this room as already processed
        if room.sp_ticket_id:
            orphan_tickets.append(room.sp_ticket_id)

    return orphan_tickets

def guest_update(guest_obj, otp, room, og_guest=None):
    ticket_code = guest_obj.ticket_code
    email = guest_obj.email
    guest = None
    try:
        # placed rooms may already have records
        # also sometimes people transfer rooms to themselves
        #   because why the frak not
        guest = Guest.objects.get(ticket=ticket_code,
                                  email=email)
        msg = f"Found existing ticket {ticket_code} for {email}, assigned to {room.name_hotel} {room.name_take3}"
        logger.debug(msg)

    except Guest.DoesNotExist:
        # but most of the time the guest does not exist yet
        guest = Guest(name=f"{guest_obj.first_name} {guest_obj.last_name}".title(),
                      ticket=guest_obj.ticket_code,
                      jwt=otp,
                      email=email)

        if guest_obj.transferred_from_code:
            guest.transfer = guest_obj.transferred_from_code

        logger.debug("New guest %s in %s room %s (%s)",
                     email, room.name_hotel, room.number, room.name_take3)

    if room.name_hotel == 'Ballys':
        guest.can_login = True

    # save guest (if needed) and then...
    if guest.is_dirty():
        guest.save()

    # update sp_ticket_id for placed rooms, this will happen
    # when processing transfers
    if room.is_placed \
       and room.sp_ticket_id \
       and room.sp_ticket_id != guest.ticket:
        logger.debug("Updating room %s sp_ticket_id %s -> %s",
                     room.number, room.sp_ticket_id, guest.ticket)
        room.sp_ticket_id = guest.ticket

    # update room
    room.guest = guest
    room.is_available = False

    if not room.resident(guest):
        room.resident_add(guest.name)

    if room.is_dirty(check_relationship=True):
        room.save()

def create_guest_entries(guest_rows, room_meta, orphan_tickets=[]):
    transferred_tickets = []

    for guest_obj in guest_rows:
        guest_entries = Guest.objects.filter(email=guest_obj.email)
        trans_code = guest_obj.transferred_from_code
        ticket_code = guest_obj.ticket_code

        if ticket_code in transferred_tickets:
            logger.debug("Skipping transferred ticket %s", ticket_code)
            continue

        if ticket_code in orphan_tickets:
            logger.debug("Skipping ticket %s from orphan processing", ticket_code)
            continue

        if trans_code == '' and guest_entries.count() == 0:
            # Unknown ticket, no transfer; new user
            room = find_room(guest_obj.product)
            if not room:
                # this should only happen if we have actually run out of inventory
                # which if we are properly tracking room inventory should not happen.
                # note it *could* also happen with data corruption or a transfer has occured
                # for a placed room and the room itself not being updated
                logger.warning("No empty rooms for product %s available for %s",
                               guest_obj.product, guest_obj.email)
                room_meta.shortage(Room.short_product_code(guest_obj.product))
                continue

            logger.debug("Guest does not exist for %s. Creating new guest contact.", guest_obj.email)
            otp = phrasing()
            guest_update(guest_obj, otp, room)
            room_meta.allocated(room.name_take3)
        elif trans_code == '' and guest_entries.count() > 0:
            # Unknown ticket, no transfer, already at least a user record. When this
            # happens we make sure that none of the user entries are associated
            # with this particular ticket before finding them a room.
            # There are a few cases that could pop up here
            # * admins / staff
            # * people may have multiple rooms
            # * people share email addresses and soft-transfer rooms in sp
            #
            if guest_entries.filter(ticket = ticket_code).count() == 0:
                room = find_room(guest_obj.product)
                if not room:
                    logger.warning("No empty rooms for product %s available for %s",
                                   guest_obj.product,
                                   guest_entries[0].email)
                    room_meta.shortage(Room.short_product_code(guest_obj.product))
                    continue

                logger.debug("assigning room %s to (unassigned ticket/room) %s",
                             room.number, guest_entries[0].email)
                guest_update(guest_obj, guest_entries[0].jwt, room)
                room_meta.allocated(room.name_take3)
            else:
                room_meta.warning(f"Not sure how to handle non-transfer, existing user ticket {ticket_code}")

        elif trans_code != "":
            # Transfered ticket...
            existing_guest = None
            transfer_room = None
            # start by loading the original owner of the room; who is transfering it
            try:
                existing_guest = Guest.original_room(trans_code)
            except Guest.DoesNotExist:
                # This may happen because the non-deterministic order of the secret party exports
                # and when this happens we ensure stub users for full transfer chain
                chain = transfer_chain(trans_code, guest_rows)
                if len(chain) == 0:
                    # Data should not be this non-deterministic tho
                    room_meta.warning(f"Ticket transfer ({trans_code}) but no previous guest found")
                    continue

                for chain_guest in chain:
                    # add stub guests (if does not already exist)
                    #  note stubs still get a jwt bc the relationship between our auth and guest model
                    try:
                        _maybe_guest = Guest.objects.get(ticket=chain_guest.ticket_code)
                    except Guest.DoesNotExist:
                        stub_name = f"{chain_guest.first_name} {chain_guest.last_name}".title()
                        stub = Guest(name=stub_name,
                                     email=chain_guest.email,
                                     ticket=chain_guest.ticket_code,
                                     jwt=phrasing())
                        logger.debug("Created stub guest %s with ticket %s",
                                     chain_guest.email, chain_guest.ticket_code)

                        if chain_guest.transferred_from_code:
                            stub.transfer = chain_guest.transferred_from_code

                        stub.save()

                        transferred_tickets.append(chain_guest.ticket_code)

                # Now that the transfer chain exists, we can figure out who most
                # recently owned the room. Note the room may or may not have
                # already been assigned!
                existing_guest = Guest.objects.get(ticket=chain[-1].ticket_code)
                transfer_room = None
                transfer_rooms = Room.objects.filter(guest = existing_guest)
                if transfer_rooms.count() > 1:
                    logger.error("Multiple rooms (%s) found for %s guest entry",
                                 ','.join([f"{x.name_hotel} {x.number}" for x in transfer_rooms]),
                                 existing_guest.email)
                    continue
                elif transfer_rooms.count() == 0:
                    transfer_room = find_room(guest_obj.product)
                    if not transfer_room:
                        logger.warning("No empty rooms of product %s available for %s",
                                       guest_obj.product,
                                       guest_obj.email)
                        room_meta.shortage(Room.short_product_code(guest_obj.product))
                        continue

                email_chain = ','.join([x.email for x in chain])
                # Ensure the guest record exists either way. For existing, we copy the
                # jwt around, otherwise we make a new one.
                if guest_entries.count() == 0:
                    logger.debug("Processing transfer %s (%s) from %s to (new guest) %s",
                                 trans_code,
                                 ticket_code,
                                 email_chain,
                                 guest_obj.email)
                    otp = phrasing()
                    guest_update(guest_obj, otp, transfer_room)
                else:
                    logger.debug("Processing transfer %s (%s) from %s to %s",
                                 trans_code,
                                 ticket_code,
                                 email_chain,
                                 guest_obj.email)
                    otp = guest_entries[0].jwt
                    guest_update(guest_obj, otp, transfer_room)

                room_meta.allocated(transfer_room.name_take3)
                room_meta.transfer(transfer_room.name_take3)

                continue

            existing_room = None
            try:
                existing_room = Room.objects.get(guest=existing_guest)
            except Room.DoesNotExist:
                logger.debug("Unable to find existing room for %s" % existing_guest)
                continue

            if guest_entries.count() == 0:
                # Transferring to new guest...
                logger.debug("Processing placed transfer %s (%s) from %s to (new guest) %s",
                             trans_code,
                             ticket_code,
                             existing_guest.email,
                             guest_obj.email)
                otp = phrasing()
                guest_update(guest_obj, otp, existing_room, og_guest=existing_guest)
            else:
                # Transferring to existing guest...
                logger.debug("Processing placed transfer %s (%s) from %s to %s",
                             trans_code,
                             ticket_code,
                             existing_guest.email,
                             guest_obj.email)
                # i think this will result in every jwt field being the same? guest entries
                # are kept around as part of transfers (ticket/email uniq) and when someone
                # has multiple rooms (email/room uniq)
                otp = guest_entries[0].jwt
                guest_update(guest_obj, otp, existing_room, og_guest=existing_guest)

            room_meta.allocated(existing_room.name_take3)
            room_meta.transfer(existing_room.name_take3)


        else:
            room_meta.error(f"Not sure how to handle ticket {ticket_code}")


@api_view(['POST'])
def create_guests(request):
    guests_csv = "%s/guestUpload_latest.csv" % roombaht_config.TEMP_DIR
    if request.method == 'POST':
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

        _guest_fields, original_guests = ingest_csv(guests_csv)

        guest_rows = [SecretPartyGuestIngest(**guest) for guest in original_guests]
        # actually keep some metrics here
        room_meta = RoomMeta()
        # start by seeing if we can address orphaned placed rooms
        orphan_tickets = reconcile_orphan_rooms(guest_rows, room_meta)
        # handle basic ingestion of guests
        create_guest_entries(guest_rows, room_meta, orphan_tickets)

        lines = room_meta.output()
        if len(lines) == 0:
            lines = ['info: No changes made.']

        logger.info("guest list uploaded by %s", auth_obj['email'])
        return Response({'csv_file': guests_csv, 'results': lines},
                        status=status.HTTP_200_OK)


@api_view(['POST'])
def run_reports(request):
    if request.method == 'POST':
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

        logger.info("reports being run by %s", auth_obj['email'])

        admin_emails = [admin.email for admin in Staff.objects.filter(is_admin=True)]
        guest_dump_file, room_dump_file = dump_guest_rooms()
        swaps_file = swaps_report()
        attachments = [
            guest_dump_file,
            room_dump_file,
            swaps_file
        ]
        for hotel in roombaht_config.GUEST_HOTELS:
            attachments.append(hotel_export(hotel))
            attachments.append(rooming_list_export(hotel))

        send_email(admin_emails,
                   'RoomService RoomBaht - Report Time',
                   'Your report(s) are here. *theme song for Brazil plays*',
                   attachments)

        return Response({"admins": admin_emails}, status=status.HTTP_201_CREATED)


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
        # rooms available: has not yet been placed, roombaht or other
        rooms_available = rooooms.exclude(is_available=False).count()
        # rooms placed by roombot: rooms available to be placed by
        rooms_placed_by_roombot = rooooms.filter(is_placed=False).count()
        rooms_placed_manually = rooooms.filter(is_placed=True).count()
        rooms_swap_code_count = rooooms.filter(swap_code__isnull=False).count()

        if(rooms_occupied!=0 and rooms_count!=0):
            percent_placed = round(float(rooms_occupied) / float(rooms_count) * 100, 2)
        else:
            percent_placed = 0

        room_metrics = []
        for room_type in ROOM_LIST.keys():
            room_total = rooooms.filter(name_take3=room_type).count()
            if room_total > 0:
                room_metrics.append({
                    "room_type": f"{ROOM_LIST[room_type]['hotel']} - {room_type}",
                    "total": room_total,
                    "unoccupied": rooooms.filter(name_take3=room_type, is_available=True).count()
                })

        metrics = {"guest_count": guest_count,
                   "guest_unique": guest_unique,
                   "guest_unplaced": guest_unplaced,
                   "rooms_count": rooms_count,
                   "rooms_occupied": rooms_occupied,
                   "rooms_swappable": rooms_swappable,
                   "rooms_available": rooms_available,
                   "rooms_placed_by_roombot": rooms_placed_by_roombot,
                   "rooms_placed_manually": rooms_placed_manually,
                   "percent_placed": int(percent_placed),
                   "rooms_swap_code_count": rooms_swap_code_count,
                   "rooms_swap_success_count": diff_swaps_count(),
                   "rooms": room_metrics,
                   "version": roombaht_config.VERSION.rstrip()
                   }

        return Response(metrics, status=status.HTTP_201_CREATED)


def validate_sp_row():
    """
    This function returns a function used to generate individual
    sp export rows based on sku / product derivations
    """

    # build a list of products that we actually care about
    # these are used for validation of specific sp export rows
    room_products = []
    for _take3_product, hotel_details in ROOM_LIST.items():
        for product in hotel_details.get('rooms', []):
            room_products.append(product)

    def validate(row):
        # if we don't know the product, drop it
        if row['product'] not in room_products:
            logger.debug("Ticket %s has product we don't care about: %s",
                         row['ticket_code'],
                         row['product'])
            return False

        if Room.derive_hotel(row['product']) not in roombaht_config.GUEST_HOTELS:
            logger.debug("Unable to derive hotel for tx %s: %s",
                         row['ticket_code'],
                         row['product'])
            return False

        # we may want to ignore this transaction
        if row['ticket_code'] in roombaht_config.IGNORE_TRANSACTIONS:
            logger.debug("Skipping ticket %s as it is on our ignore list",
                         row['ticket_code'])
            return False

        # we will not process any transactions more than once
        existing_ticket = None

        try:
            existing_ticket = Guest.objects.get(ticket=row['ticket_code'])
        except Guest.DoesNotExist:
            pass

        if existing_ticket:
            logger.debug("[-] Ticket %s from upload already in db",
                           row['ticket_code'])
            return False

        return True

    return validate

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
        guest_fields, original_guests = ingest_csv(rows)
        guests = []

        # basic input validation, make sure it's the right csv
        if 'ticket_code' not in guest_fields or \
           'product' not in guest_fields:
            return Response("Unknown file", status=status.HTTP_400_BAD_REQUEST)

        # figure out how to handle sku/product consistently between years
        # until then, strip out the parts roombaht don't care about
        for o_guest in original_guests:
            raw_product = o_guest['product']
            o_guest['product'] = re.sub(r'[\d\.]+ RS24 ', '', raw_product)
            guests.append(o_guest)

        row_validator = validate_sp_row()
        for guest in guests:
            if not row_validator(guest):
                continue

            new_guests.append(guest)

        if len(new_guests) > 0 and len(new_guests) != len(guests):
            logger.info("Processing partial upload. %s entries - %s",
                        len(new_guests), ','.join([x['ticket_code'] for x in new_guests]))

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

@api_view(['POST'])
def fetch_reports(request):
    if request.method == 'POST':
        auth_obj = authenticate_admin(request)
        if not auth_obj or 'email' not in auth_obj or not auth_obj['admin']:
            return unauthenticated()

    if 'report' not in request.data or \
       'hotel' not in request.data:
        return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)

    if request.data['hotel'].title() not in roombaht_config.GUEST_HOTELS:
        return Response("unknown hotel", status=status.HTTP_400_BAD_REQUEST)

    export_file = None
    if request.data['report'] == 'hotel':
        export_file = hotel_export(request.data['hotel'])
    elif request.data['report'] == 'roomslist':
        export_file = rooming_list_export(request.data['hotel'])
    elif request.data['report'] == 'room':
        _guest_file, export_file = dump_guest_rooms()
    elif request.data['report'] == 'guest':
        export_file, _room_file = dump_guest_rooms()
    elif request.data['report'] == 'swaps':
        export_file = swaps_report()
    else:
        return Response("unknown report", status=status.HTTP_400_BAD_REQUEST)

    response = HttpResponse(open(export_file, 'r'), content_type='text/csv')
    response['Content-Disposition'] = f"attachment; filename={os.path.basename(export_file)}"

    return response
