
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

logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

logger = logging.getLogger('ViewLogger_admin')

RANDOM_ROOMS = os.environ.get('RANDOM_ROOMS', True)

def assign_room(type_purchased_secpty):
    types2023RoomList = {
        'Queen': [
          'Hard Rock - Standard 2 Queens (50% fee)',
          'Hard Rock - Lakeview 2 Queens',
          'Hard Rock - Lakeview 2 Queens (Post Sale)',
          'Hard Rock - Lakeview Balcony 2 Queens',
          "Bally's - Standard 2 Queens",
          "Bally's - Standard 2 Queens (50% fee)",
          "Bally's - Standard 2 Queens (Direct Sale)",
          "Bally's - Standard 2 Queens (Post Sale)",
          "Bally's - Standard 2 Queens (RFP Sale)",
        ],
        
        'Queen Sierra Suite': [
          "Bally's - Sierra 2 Queens Suite",
        ],
        
        "King": [
          'Hard Rock - Standard King',
          'Hard Rock - Standard King (Post Sale)',
          'Hard Rock - Standard King (RFP Sale)'
          'Hard Rock - Lakeview King',
          'Hard Rock - Lakeview Balcony King',
          'Hard Rock - Lakeview Balcony King (Post Sale)',
          'Hard Rock - Balcony King',
          'Hard Rock - Balcony King (RFP Sale)',
          "Bally's - Standard King",
          "Bally's - Standard King (Direct Sale)",
          "Bally's - Standard King (Post Sale)",
          "Bally's - Standard King (RFP Sale)",
        ],
        
        'King Sierra Suite': [
          "Bally's - Sierra King Suite",
          "Bally's - Sierra King Suite (Post Sale)",
         ],
        
        'Tahoe Suite': [
          "Bally's - Tahoe King Suite",
          "Bally's - Tahoe King Suite (Post Sale)",
        ],
        
        "Executive Suite": [
          "Bally's - Executive King Suite",
        ],

    }
    for roomtype in types2023RoomList.items():
        if(type_purchased_secpty in roomtype[1]):
            set_room = roomtype[0]
            break
        else:
            set_room = "Room type not found"


    if(RANDOM_ROOMS=="TRUE"):
        rooms = Room.objects.all()
        #no_guest=list(filter(lambda x:x.guest==None, rooms))
        no_guest = Room.objects.filter(guest=None)
        for room in no_guest:
            if(room.name_take3 == set_room):
                logger.info(f"[+] Assigned room number: {room.number}")
                return room
            else:
                pass
        #logger.warn(f'[-] No room of matching type available. looking for: {type_purchased_secpty} remainging inventory:\nTake3names: {[elem.name_take3 for elem in no_guest]}\nHotel names: {[elem.name_hotel for elem in no_guest]}')
        logger.warn(f'[-] No room of matching type available. looking for: {type_purchased_secpty} ')
        return None
    else:
        # testing purposes
        logger.warning(f'test room assigned in create')
        return Room(number=666)


def guest_sort(guest_list):
    ''' merge sort by email. u know wat time it is '''
    if (len(guest_list)>1):
        mid = len(guest_list)//2
        L = guest_list[:mid]
        R = guest_list[mid:]
        guest_sort(L)
        guest_sort(R)
        i = j = k = 0
        while i<len(L) and j<len(R):
            if L[i].email.lstrip() <= R[j].email.lstrip():
                guest_list[k] = L[i]
                i += 1
            else:
                guest_list[k] = R[j]
                j += 1
            k += 1
        while i < len(L):
            guest_list[k] = L[i]
            i += 1
            k += 1
        while j < len(R):
            guest_list[k] = R[j]
            j += 1
            k += 1


def guest_search(arr, low, high, x):
    ''' binary search by email '''
    if high >= low:
        mid = (high + low) // 2
        if arr[mid].email == x:
            return arr[mid]
        elif arr[mid].email > x:
            return guest_search(arr, low, mid - 1, x)
        else:
            return guest_search(arr, mid + 1, high, x)
    else:
        return None


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
    room.save()

    logger.info(f"[+] Assigned room number: {room.number}")
    if(email_onboarding):
        time.sleep(5)
        if os.environ.get('ROOMBAHT_SEND_MAIL', 'FALSE').lower() == 'true':
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


def create_guest_entries(init_file=""):
    guest_rows = []
    guests_existing = list(Guest.objects.all())
    guest_sort(guests_existing)
    try:
        glen = len(guests_existing)-1
    except TypeError as e:
        logger.warning(f"No existing guests to show ")
        glen=0

    with open(init_file, "r") as f1:
        for row in DictReader(f1):
            stripd = {k.lstrip().rstrip(): v.lstrip().rstrip() for k, v in row.items() if type(k)==str and type(v)==str}
            guest_rows.append(stripd)

    characters = string.ascii_letters + string.digits + string.punctuation
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
            otp = ''.join(random.choice(characters) for i in range(10))
            guest_contact_new(guest_new, otp, email_onboarding=True)
        # Update from ticket transfer
        elif(trans_code!=""):
            try:
                existing_guest = Guest.objects.filter(ticket=trans_code)[0]
            except IndexError as e:
                logger.warn(f'[-] Ticket transfer but no previous ticket id found')
                continue
            existing_room = existing_ticket.room
            logger.info(f'Ticket is a transfer. ')
            otp = ''.join(random.choice(characters) for i in range(10))
            if(len(guest_entries)==0):
                guest_contact_new(guest_new, otp, email_onboarding=True, room=existing_room)
            else:
                guest_contact_new(guest_new, otp, email_onboarding=False, room=existing_room)
            existing_guest.delete()
        # Create without email
        else:
            if(len(tix_exist)==0):
                logger.info(f'Email exists. Creating new ticket.')
                otp = ''.join(random.choice(characters) for i in range(10))
                guest_contact_new(guest_new, otp, email_onboarding=False)


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
        if(validate_admin(data)==True):
            create_guest_entries(init_file=guests_csv)

            return Response(str(json.dumps({"Creating guests using:": f'{guests_csv}'})),
                                             status=status.HTTP_201_CREATED)
        else:
            return Response("User not admin", status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def run_reports(request):
    if request.method == 'POST':
        data = request.data["data"]
        logger.info(f'Run reports attempt')
        if(validate_admin(data)==True):
            admin_emails = Staff.objects.filter(is_admin=True)
            dump_guest_rooms()
            if os.environ.get('ROOMBAHT_SEND_MAIL', 'FALSE').lower() == 'true':
                logger.info(f'sending admin emails: {admin_emails}')
                conn = get_connection()
                msg = EmailMessage(subject="RoomBaht Report",
                                   body="Diff dump, guest dump, room dump",
                                   to=[admin.email for admin in admin_emails],
                                   connection=conn)
                #TODO(tb) verify these files
                msg.attach_file("%s/guest_dump.csv" % os.environ['ROOMBAHT_TMP'])
                msg.attach_file("%s/room_dump.csv" % os.environ['ROOMBAHT_TMP'])
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
            guest_unique = len(set([guest.email for guest in Guest.objects.all()]))
            guest_count = len(Guest.objects.all())
            rooms_count = len(Room.objects.all())
            rooms_occupied = Room.objects.filter(guest__isnull=False).count();
            resp = str(json.dumps({"guest_count": guest_count,
                                   "rooms_count": rooms_count,
                                   "rooms_occupied": rooms_occupied,
                                   "guest_unique": guest_unique,
                                   }))
            return Response(resp, status=status.HTTP_201_CREATED)
        else:
            return Response("User not admin", status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def guest_file_upload(request):
    if request.method == 'POST':
        data = request.data["guest"]
        if(validate_admin(data)==True):
            logger.info(f'guest upload: {data["guest_list"]}')
            rows = data['guest_list'].split('\n')
            diff_count = diff_latest(rows)

            with open("%s/guestUpload_latest.csv" % os.environ['ROOMBAHT_TMP'] , 'w') as fout:
                for elem in rows:
                    guest_new = elem.split(",")
                    existing_ticket = Guest.objects.filter(ticket=guest_new[0])
                    if(len(existing_ticket)!=1):
                        fout.write(elem+"\n")
                    else:
                        logger.warn(f'[-] Ticket from upload already in db: {elem}')

            resp = str(json.dumps({"received_rows": len(rows),
                                   "headers": rows[0] ,
                                   "first_row": rows[1] ,
                                   "diff": diff_count,
                                   "status": "Ready to Load..."
                                   }))
            return Response(resp, status=status.HTTP_201_CREATED)
        else:
            return Response("User not admin", status=status.HTTP_400_BAD_REQUEST)
