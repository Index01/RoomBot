import argparse
import logging
import os
import random
import termios
import tty
import string
import sys

import django
django.setup()
from reservations.models import Guest, Room, Staff
from django.core.mail import send_mail
from django.core.mail import EmailMessage, get_connection
from django.forms.models import model_to_dict
from csv import DictReader, DictWriter
import time

logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

logger = logging.getLogger('createStaffAndRooms')

def getch():
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    return _getch()

def search_ticket(ticket, guest_entries):
    while(len(guest_entries)>0):
        guest = guest_entries.pop()
        logger.debug(f'guest.ticket: {guest.ticket}, ticket: {ticket}')
        if(guest.ticket == ticket):
            return True
        else:
            continue
    return False


def create_rooms_main(init_file =""):
    rooms=[]
    rooms_rows = []
    types2023RoomListUnique = {
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
        
        "Executive Suite": [
         "Bally's - Executive King Suite",
        ],
        
        'Tahoe Suite': [
         "Bally's - Tahoe King Suite",
         "Bally's - Tahoe King Suite (Post Sale)",
        ],
        
        'King Sierra Suite': [
         "Bally's - Sierra King Suite",
         "Bally's - Sierra King Suite (Post Sale)",
         ]
    }

    with open(init_file, "r") as f1:
        for elem in DictReader(f1):
            elem = {x.lstrip(): v for x, v in elem.items()}
            elem = {x: v.replace(' ', '') for x, v in elem.items() if type(v)==str}
            rooms_rows.append(elem)

    for elem in rooms_rows:
        if(elem["Placed_by"]=="Roombaht"):
            for roomtype in types2023RoomList:
                if(elem["Room Type"] in roomtype[1]):
                    setRoom = roomtype[0]
                else:
                    setRoom = None
            rooms.append(Room(name_take3=setRoom,
                              name_hotel=elem['Room Type'],
                              number=elem['Number'],
                              available=True
                              )
                        )
        else:
            logger.debug(f'[-] Room excluded by ROOMBAHT colum: {elem}')

    logger.debug(f'swappable rooms: {rooms}')
    list(map(lambda x: x.save(), rooms))


def create_staff(init_file=None):
    dr = None
    with open(init_file, "r") as f1:
        dr = []
        for elem in DictReader(f1):
            dr.append(elem)
    for staff_new in dr:
        characters = string.ascii_letters + string.digits + string.punctuation
        otp = ''.join(random.choice(characters) for i in range(10))
        guest=Guest(name=staff_new['name'],
            email=staff_new['email'],
            ticket=666,
            jwt=otp)
        guest.save()

        staff=Staff(name=staff_new['name'],
            email=staff_new['email'],
            guest=guest,
            is_admin=staff_new['is_admin'])
        staff.save()

        logger.info(f"[+] Created staff: {staff_new['name']}, {staff_new['email']}, otp: {otp}, isadmin: {staff_new['is_admin']}")

        hostname = os.environ['ROOMBAHT_HOST']

        if os.environ.get('ROOMBAHT_SEND_MAIL', 'FALSE').lower() == 'true':
            logger.debug(f'[+] Sending invite for staff member {staff_new["email"]}')

            body_text = f"""
                Congratulations, u have been deemed Staff worthy material.

                Email {staff_new['email']}
                Admin {otp}

                login at http://{hostname}/login
                then go to http://{hostname}/admin
                Good Luck, Starfighter.

            """
            send_mail("RoomService RoomBaht",
                      body_text,
                      os.environ['ROOMBAHT_EMAIL_HOST_USER'],
                      [staff_new["email"]],
                      auth_user=os.environ['ROOMBAHT_EMAIL_HOST_USER'],
                      auth_password=os.environ['ROOMBAHT_EMAIL_HOST_PASSWORD'],
                      fail_silently=False)


def main(args):

    if len(Room.objects.all()) > 0 or \
       len(Staff.objects.all()) > 0 or \
       len(Guest.objects.all()) > 0:
        if not args['force']:
            print('Overwrite data? [y/n]')
            if getch().lower() != 'y':
                raise Exception('user said nope')
        else:
            logger.warning('Overwriting data at user request!')

    Room.objects.all().delete()
    Staff.objects.all().delete()
    Guest.objects.all().delete()

    create_rooms_main(init_file=args['rooms_file'])
    create_staff(init_file=args['staff_file'])

if __name__=="__main__":
    parser = argparse.ArgumentParser(usage=('like db fixtures but not'),
                                     description='create staff and rooms')
    parser.add_argument('rooms_file',
                        help='Path to Rooms CSV file')
    parser.add_argument('staff_file',
                        help='Path to Staff CSV file')
    parser.add_argument('--force',
                        dest='force',
                        help='Force overwriting',
                        action='store_true',
                        default=False)

    args = vars(parser.parse_args())
    main(args)
