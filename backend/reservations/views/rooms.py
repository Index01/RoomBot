
import os
import logging
import environ
import random
import json
import jwt
import datetime
import sys
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from ..models import Guest
from ..models import Room
from ..serializers import *

logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

logger = logging.getLogger('ViewLogger_rooms')

SEND_MAIL = os.environ['ROOMBAHT_SEND_MAIL']

def validate_jwt(jwt_data):
    env = environ.Env()
    environ.Env.read_env()
    try:
        key = env("ROOMBAHT_JWT_KEY")
    except ImproperlyConfigured as e:
        logger.error("env key fail")
        return None

    try:
        dec = jwt.decode(jwt_data, key, algorithms="HS256")
    except (TypeError, jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError) as e:
        return None

    dthen = datetime.datetime.fromisoformat(dec["datetime"])
    dnow = datetime.datetime.utcnow()

    if (dnow - dthen > datetime.timedelta(days=1)):
        return None
    else:
        return dec["email"]


def phrasing():
    words = None
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open("%s/../../config/wordylyst.md" % dir_path , "r") as f:
        words = [word for word in f.read().splitlines()]
    word = words[random.randint(0, 999)].capitalize()+words[random.randint(0, 999)].capitalize()
    rand = random.randint(1,3)
    if(rand==1):
        word = word+str(random.randint(0,99))
    elif(rand==2):
        word = word+str(random.randint(0,99))+words[random.randint(0,999)].capitalize()
    else:
        word = word+words[random.randint(0,999)].capitalize()
    return word


@api_view(['POST'])
def my_rooms(request):
    if request.method == 'POST':
        data = request.data
        try:
            jwt_data=data["jwt"]
        except KeyError as e:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)

        email = validate_jwt(jwt_data)
        if (email is None):
            return Response("Invalid jwt", status=status.HTTP_400_BAD_REQUEST)

        try:
            guest_instances = Guest.objects.filter(email=email)
            guest_id = guest_instances[0].id
        except IndexError as e:
            return Response("No guest or room found", status=status.HTTP_400_BAD_REQUEST)

        rooms = Room.objects.all()
        rooms_mine = [elem for elem in rooms if elem.guest!=None and elem.guest.email==email]
        room_nums = [int(room.number) for room in rooms]

        response = json.dumps([{"number": int(room.number),
                                "type": room.name_take3} for room in rooms_mine], indent=2)

        logger.debug(f'my_rooms: {rooms_mine}')
        return Response(response)


@api_view(['POST'])
def room_list(request):
    if request.method == 'POST':
        req = request.data
        try:
            jwt_data=req["jwt"]
        except KeyError as e:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)
        email = validate_jwt(jwt_data)
        if (email is None):
            return Response("Invalid jwt", status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"[+] Valid guest viewing rooms: {email}")
        rooms = Room.objects.all()

        #no_guest = list(filter(lambda x:x.guest==None, rooms))
        #for elem in no_guest:
        #    elem.available=False
        #    elem.save()

        rooms = Room.objects.all()

        serializer = RoomSerializer(rooms, context={'request': request}, many=True)
        data = serializer.data

        floorplans = {
                3: ["ballys_3rd.png", "ballys_3rd_thumb.png"],
                4: ["ballys_4th.png", "ballys_4th_thumb.png"],
                5: ["ballys_5th.png", "ballys_5th_thumb.png"],
                6: ["ballys_6th.png", "ballys_6th_thumb.png"],
                7: ["ballys_7th.png", "ballys_7th_thumb.png"],
                8: ["ballys_8th.png", "ballys_8th_thumb.png"],
                9: ["ballys_9th.png", "ballys_9th_thumb.png"],
                10: ["ballys_10th.png", "ballys_10th_thumb.png"],
                11: ["ballys_11th.png", "ballys_11th_thumb.png"],
                12: ["ballys_12th.png", "ballys_12th_thumb.png"],
                13: ["ballys_13th.png", "ballys_13th_thumb.png"],
                14: ["ballys_14th.png", "ballys_14th_thumb.png"],
                15: ["ballys_15th.png", "ballys_15th_thumb.png"],
                16: ["ballys_16th.png", "ballys_16th_thumb.png"],
                17: ["ballys_17th.png", "ballys_17th_thumb.png"]
                }

        for room in data:
            if(len(room['number'])==3):
                room["floorplans"]=floorplans[int(room["number"][:1])]
            elif(len(room['number'])==4):
                room["floorplans"]=floorplans[int(room["number"][:2])]

        return Response(serializer.data)



@api_view(['POST'])
def room_reserve(request):
    if request.method == 'POST':
        #TODO(tb): there is prolly a more standard way of doing this. serializer probs tho.
        data = request.data['guest']
        logger.debug(f'data: {data}')
        try:
            jwt_data=data["jwt"]['jwt']
            room_number = data["number"]
        except KeyError as e:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)

        email = validate_jwt(jwt_data)
        if (email is None):
            return Response("Invalid jwt", status=status.HTTP_400_BAD_REQUEST)

        try:
            guest = Guest.objects.filter(email=email)
            room = Room.objects.filter(number=room_number)
            room.update(available=False, guest=guest[0])
            room[0].save()
        except IndexError as e:
            return Response("No guest or room found", status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
def room_detail(request, pk):
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
        data = request.data["guest"]
        try:
            jwt_data=data["jwt"]
            room_num=data["number"]
            msg=data["contact_info"]
        except KeyError as e:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)
        requester_email = validate_jwt(jwt_data)
        if (requester_email is None):
            return Response("Invalid jwt", status=status.HTTP_400_BAD_REQUEST)
        swap_req = Room.objects.filter(number=room_num)

        try:
            swap_req_email = swap_req[0].guest.email
            logger.info(f'[+] Swap request sent to: {swap_req_email}')
        except (KeyError, AttributeError) as e:
            return Response("No email found for that room", status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"[+] Sending swap req from {requester_email} to {swap_req_email} with msg: {msg}")

        body_text = f"""

Someone would like to trade rooms with you for Room Service. Since rooms are randomly assigned, we built this tool for everyone to trade rooms and get the placement they want. If you are open to trading rooms, contact this person via the info below. Sort out the details, then one of you will generate a swap code in Roombaht and send it to the other. Enter the code, switch-aroo magic happens, and you check-in as normal.

Contact info: {msg}

After you have contacted the person asking to trade rooms with you, click this link to create the swap code and trade rooms: http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:3000/rooms

If you have any trouble with that link you can login from the initial email you received from RoomBaht.

If you have any issues contact placement@take3presents.com

Good Luck, Starfighter.

        """

        if(SEND_MAIL==True):
            send_mail("RS Room Trade Request",
                      body_text,
                      "placement@take3presents.com",
                      [swap_req_email],
                      auth_user="placement@take3presents.com",
                      auth_password=os.environ['EMAIL_HOST_PASSWORD'],
                      fail_silently=False,)

        return Response("Request sent! They will respond if interested.", status=status.HTTP_201_CREATED)



@api_view(['POST'])
def swap_gen(request):
    if request.method == 'POST':
        data = request.data
        logger.debug(f"data_swap_gen: {data}")
        try:
            jwt_data=data["jwt"]
            room_num=data["number"]
        except KeyError as e:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)
        email = validate_jwt(jwt_data)
        if (email is None):
            return Response("Invalid jwt", status=status.HTTP_400_BAD_REQUEST)
        try:
            guest_instances = Guest.objects.filter(email=email)
            guest_id = guest_instances[0].id
        except IndexError as e:
            return Response("No guest found", status=status.HTTP_400_BAD_REQUEST)
        #rooms = Room.objects.filter(guest=guest_id)
        rooms = Room.objects.filter(number=room_num)
        phrase = phrasing()
        for room in rooms:
            if(str(room_num) == str(room.number) ):
                room.swap_code=phrase
                room.swap_time=datetime.datetime.utcnow()
                room.save()

        logger.info(f"[+] Swap phrase generated {phrase}")
        response = json.dumps({"swap_phrase": phrase}, indent=2)
        return Response(response)


@api_view(['POST'])
def swap_it_up(request):
    if request.method == 'POST':
        data = request.data
        try:
            jwt_data=data["jwt"]
            room_num=data["number"]
            swap_req=data["swap_code"]
        except KeyError as e:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)
            logger.error(f"Missing fields")
        email = validate_jwt(jwt_data)

        logger.info(f"[+] Swap attempt {data}")
        if (email is None):
            return Response("Invalid jwt", status=status.HTTP_400_BAD_REQUEST)
        try:
            guest_instances = Guest.objects.filter(email=email)
            guest_id = guest_instances[0].id
        except IndexError as e:
            logger.warning(f"[+] No guest found")
            return Response("No guest found", status=status.HTTP_400_BAD_REQUEST)

        rooms_swap_match = Room.objects.filter(swap_code=swap_req)
        swap_room_mine = Room.objects.filter(number=room_num)[0]
        logger.info(f"[+] Swap match {rooms_swap_match}")
        try:
            swap_room_theirs = rooms_swap_match[0]
        except IndexError as e:
            logger.warning("[-] No room matching code")
            return Response("No room matching that code", status=status.HTTP_400_BAD_REQUEST)

        expiration = swap_room_theirs.swap_time+datetime.timedelta(seconds=600)
        if(expiration.timestamp() < datetime.datetime.utcnow().timestamp()):
            logger.warning("[-] Expired swap code")
            return Response("Expired code", status=status.HTTP_400_BAD_REQUEST)

        guest_id_theirs = swap_room_theirs.guest
        swap_room_theirs.guest = swap_room_mine.guest
        swap_room_mine.guest = guest_id_theirs

        logger.info(f"[+] Weve got a SWAPPA!!! {swap_room_mine} {swap_room_theirs}")
        swap_room_mine.save()
        swap_room_theirs.save()

        return Response(status=status.HTTP_201_CREATED)


