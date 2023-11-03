
import os
import logging
import random
import json
import datetime
import sys
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.utils.timezone import make_aware
from ..models import Guest
from ..models import Room
from ..serializers import *
from ..helpers import phrasing
from ..constants import FLOORPLANS
from ..reporting import diff_swaps
from reservations.helpers import my_url, send_email
import reservations.config as roombaht_config
from reservations.auth import authenticate, unauthenticated

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger('ViewLogger_rooms')

@api_view(['POST'])
def my_rooms(request):
    if request.method == 'POST':
        auth_obj = authenticate(request)
        if not auth_obj or 'email' not in auth_obj:
            return unauthenticated()

        email = auth_obj['email']

        try:
            _guest_instances = Guest.objects.filter(email=email)
        except IndexError:
            return Response("No guest or room found", status=status.HTTP_400_BAD_REQUEST)

        rooms = Room.objects.filter(name_hotel='Ballys')
        rooms_mine = [elem for elem in rooms if elem.guest is not None and elem.guest.email==email]

        data = {
            'rooms': [{"number": int(room.number),
                       "type": room.name_take3,
                       "swappable": room.swappable()} for room in rooms_mine],
            'swaps_enabled': roombaht_config.SWAPS_ENABLED
        }

        response = json.dumps(data, indent=2)

        logger.debug("rooms for user %s: %s", email, rooms_mine)
        return Response(response)


@api_view(['POST'])
def room_list(request):
    if request.method == 'POST':
        auth_obj = authenticate(request)
        if not auth_obj or 'email' not in auth_obj:
            return unauthenticated()

        email = auth_obj['email']
        logger.debug("Valid guest %s viewing rooms", email)
        # we want to bubble up any room that is swappable, is not available,
        #  is not special (chapel, etc), and does have a guest associated.
        #  the display layer will handle the per-room-type filtering
        rooms = Room.objects \
                    .filter(is_swappable=True,
                            is_available=False,
                            is_special=False,
                            name_hotel='Ballys') \
                    .exclude(guest=None)
        guest_entries = Guest.objects.filter(email=email)
        room_types = []
        guest_room_numbers = [guest.room_number
                       for guest in guest_entries
                       if guest.room_number is not None]
        for guest_room_number in guest_room_numbers:
            try:
                guest_room = Room.objects.get(number=guest_room_number, name_hotel='Ballys')
                if guest_room.name_take3 not in room_types \
                   and guest_room.swappable():
                    room_types.append(guest_room.name_take3)
            except Room.ObjectNotFound:
                logger.warning("Guest room %s not found for %s", guest_room_number, email)

        if len(room_types) == 0:
            logger.debug("No room types available for guest %s", email)

        not_my_rooms = [x for x in rooms if x.guest.email != email]
        serializer = RoomSerializer(not_my_rooms, context={'request': request}, many=True)
        data = {
            'rooms': serializer.data,
            'swaps_enabled': roombaht_config.SWAPS_ENABLED
        }

        for room in data['rooms']:
            if(len(room['number'])==3):
                room["floorplans"]=FLOORPLANS[int(room["number"][:1])]
            elif(len(room['number'])==4):
                room["floorplans"]=FLOORPLANS[int(room["number"][:2])]

            if roombaht_config.SWAPS_ENABLED and room['name_take3'] in room_types:
                room['available']=True
            else:
                room['available']=False

        return Response(data)


@api_view(['POST'])
def room_reserve(request):
    if request.method == 'POST':
        auth_obj = authenticate(request)
        if not auth_obj or 'email' not in auth_obj:
            return unauthenticated()

        #TODO(tb): there is prolly a more standard way of doing this. serializer probs tho.
        data = request.data['guest']
        logger.debug(f'data: {data}')

        try:
            guest = Guest.objects.filter(email=email)
            room = Room.objects.filter(number=room_number, name_hotel='Ballys')
            room.update(is_available=False, guest=guest[0])
            room[0].save()
        except IndexError as e:
            return Response("No guest or room found", status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
def room_detail(request, pk):
    auth_obj = authenticate(request)
    if not auth_obj or 'email' not in auth_obj:
        return unauthenticated()
    try:
        room = Room.objects.get(pk=pk)
    except Room.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = RoomSerializer(room, data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['POST'])
def swap_request(request):
    if request.method == 'POST':
        auth_obj = authenticate(request)
        if not auth_obj or 'email' not in auth_obj:
            return unauthenticated()

        requester_email = auth_obj['email']

        data = request.data

        if not roombaht_config.SWAPS_ENABLED:
            return Response("Room swaps are not currently enabled",
                            status=status.HTTP_501_NOT_IMPLEMENTED)

        try:
            room_num=data["number"]
            msg=data["contact_info"]
        except KeyError:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)

        requester_room_numbers = [x.room_number
                                  for x in Guest.objects.filter(email=requester_email,
                                                                room_number__isnull=False)]

        swap_room = None
        try:
            swap_room = Room.objects.get(number=room_num, name_hotel='Ballys')
        except Room.ObjectNotFound:
            return Response("Room not found", status=status.HTTP_404_NOT_FOUND)

        if not swap_room.swappable():
            return Response(f"Room {swap_room.number} is not swappable",
                            status=status.HTTP_400_BAD_REQUEST)

        requester_swappable = []
        for room_number in requester_room_numbers:
            try:
                room = Room.objects.get(number=room_number, name_hotel='Ballys')
                if room.name_take3 == swap_room.name_take3 and room.swappable():
                    requester_swappable.append(room_number)
            except Room.ObjectNotFound:
                logger.warning("Guest %s has non existent room %s!",
                               requester_email, room_number)
                continue

        if len(requester_swappable) == 0:
            return Response(f"Requester {requester_email} has no swappable rooms for {room_num}",
                            status=status.HTTP_400_BAD_REQUEST)

        logger.info("[+] Sending swap req from %s to %s with msg: %s",
                    requester_email,
                    swap_room.guest.email,
                    msg)

        hostname = my_url()
        body_text = f"""

Someone would like to trade rooms with you for Room Service. Since rooms are randomly placed, we built this tool to let people swap rooms and get the placement they want. If you are open to trading rooms, contact this person via the info below. Sort out the details with them, then one of you will generate a swap code in Roombaht and send it to the other. One person enters the other one’s swap code, switch-aroo magic happens, and you both check-in as normal to your new rooms.

They may swap for rooms: {','.join(requester_swappable)}
Contact info: {msg}

After you have contacted the person asking to trade rooms with you and decided to swap, click this link to create the swap code and trade rooms: {hostname}/rooms

If you have any trouble with that link, you can login from the initial email you received from RoomBaht.

If you have any issues, contact placement@take3presents.com.

Good Luck, Starfighter.

        """

        send_email([swap_room.guest.email],
                   'RoomService RoomBaht - Room Swap Request',
                   body_text)

        return Response("Request sent! They will respond if interested.", status=status.HTTP_201_CREATED)



@api_view(['POST'])
def swap_gen(request):
    if request.method == 'POST':
        auth_obj = authenticate(request)
        if not auth_obj or 'email' not in auth_obj:
            return unauthenticated()
        email = auth_obj['email']

        if not roombaht_config.SWAPS_ENABLED:
            return Response("Room swaps are not currently enabled",
                            status=status.HTTP_501_NOT_IMPLEMENTED)

        data = request.data
        logger.debug(f"data_swap_gen: {data}")
        try:
            room_num=data["number"]["row"]
        except KeyError as e:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)

        try:
            guest_instances = Guest.objects.filter(email=email)
            guest_id = guest_instances[0].id
        except IndexError as e:
            return Response("No guest found", status=status.HTTP_400_BAD_REQUEST)
        room = Room.objects.get(number=room_num, name_hotel='Ballys')
        phrase=phrasing()
        room.swap_code=phrase
        room.swap_time=make_aware(datetime.datetime.utcnow())
        room.save()

        logger.info(f"[+] Swap phrase generated {phrase}")
        response = json.dumps({"swap_phrase": phrase}, indent=2)
        return Response(response)


@api_view(['POST'])
def swap_it_up(request):
    if request.method == 'POST':
        auth_obj = authenticate(request)
        if not auth_obj or 'email' not in auth_obj:
            return unauthenticated()
        email = auth_obj['email']

        if not roombaht_config.SWAPS_ENABLED:
            return Response("Room swaps are not currently enabled",
                            status=status.HTTP_501_NOT_IMPLEMENTED)

        data = request.data
        try:
            room_num=data["number"]
            swap_req=data["swap_code"]
        except KeyError as e:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)
            logger.error(f"Missing fields")

        logger.info(f"[+] Swap attempt {data}")
        try:
            guest_instances = Guest.objects.filter(email=email)
            guest_id = guest_instances[0].id
        except IndexError as e:
            logger.warning(f"[+] No guest found")
            return Response("No guest found", status=status.HTTP_400_BAD_REQUEST)

        rooms_swap_match = Room.objects.filter(swap_code=swap_req, name_hotel='Ballys')
        swap_room_mine = Room.objects.filter(number=room_num, name_hotel='Ballys')[0]
        logger.info(f"[+] Swap match {rooms_swap_match}")
        try:
            swap_room_theirs = rooms_swap_match[0]
        except IndexError as e:
            logger.warning("[-] No room matching code")
            return Response("No room matching that code", status=status.HTTP_400_BAD_REQUEST)

        if not swap_room_mine.swappable():
            logger.warning("Attempted to swap non swappable room %s", swap_room_mine.number)
            return Response("Unable to swap rooms", status=status.HTTP_400_BAD_REQUEST)

        if not swap_room_theirs.swappable():
            logger.warning("Attempted to swap non swappable room %s", swap_room_theirs.number)
            return Response("Unable to swap rooms", status=status.HTTP_400_BAD_REQUEST)

        if swap_room_mine.name_take3 != swap_room_theirs.name_take3:
            logger.warning("Attempt to swap mismatched room types %s (%s) - %s (%s)",
                           swap_room_mine.number, swap_room_mine.name_take3,
                           swap_room_theirs.number, swap_room_theirs.name_take3)
            return Response("Unable to swap rooms", status=status.HTTP_400_BAD_REQUEST)

        expiration = swap_room_theirs.swap_time+datetime.timedelta(seconds=3600)

        if(expiration.timestamp() < make_aware(datetime.datetime.utcnow()).timestamp()):
            logger.warning("[-] Expired swap code")
            return Response("Expired code", status=status.HTTP_400_BAD_REQUEST)

        swap_room_mine.guest.room_number = swap_room_theirs.number
        swap_room_theirs.guest.room_number = swap_room_mine.number

        swap_room_theirs.swap_code = None
        guest_id_theirs = swap_room_theirs.guest
        swap_room_theirs.guest = swap_room_mine.guest
        swap_room_mine.guest = guest_id_theirs

        swap_room_theirs_primary = swap_room_theirs.primary
        swap_room_theirs_secondary = swap_room_theirs.secondary
        swap_room_theirs.primary = swap_room_mine.primary
        swap_room_mine.primary = swap_room_theirs_primary

        if swap_room_mine.secondary:
            swap_room_theirs.secondary = swap_room_mine.secondary

        if swap_room_theirs.secondary:
            swap_room_mine.secondary = swap_room_theirs_secondary

        swap_room_theirs_check_in = swap_room_theirs.check_in
        swap_room_theirs_check_out = swap_room_theirs.check_out
        swap_room_theirs.check_in = swap_room_mine.check_in
        swap_room_theirs.check_out = swap_room_mine.check_out
        swap_room_mine.check_in = swap_room_theirs_check_in
        swap_room_mine.check_out = swap_room_theirs_check_out

        swap_room_theirs_guest_notes = swap_room_theirs.guest_notes
        swap_room_theirs.guest_notes = swap_room_mine.guest_notes
        swap_room_mine.guest_notes = swap_room_theirs_guest_notes

        swap_room_theirs_sp_ticket_id = swap_room_theirs.sp_ticket_id
        swap_room_theirs.sp_ticket_id = swap_room_mine.sp_ticket_id
        swap_room_mine.sp_ticket_id = swap_room_theirs_sp_ticket_id

        logger.info(f"[+] Weve got a SWAPPA!!! {swap_room_mine} {swap_room_theirs}")
        swap_room_mine.save()
        swap_room_theirs.save()
        diff_swaps(swap_room_theirs, swap_room_mine)

        swap_room_mine.guest.save()
        swap_room_theirs.guest.save()

        return Response(status=status.HTTP_201_CREATED)
