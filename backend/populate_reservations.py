
import os
import random
import string
import django

django.setup()
from reservations.models import Guest, Room, Staff
from django.core.mail import send_mail
from django.core.mail import EmailMessage, get_connection
from django.forms.models import model_to_dict
from csv import DictReader, DictWriter
import time


def search_ticket(ticket, guest_entries):
    while(len(guest_entries)>0):
        guest = guest_entries.pop()
        print(f'guest.ticket: {guest.ticket}, ticket: {ticket}')
        if(guest.ticket == ticket):
            return True
        else:
            continue
    return False


def create_rooms(init_file =""):
    rooms=[]
    with open(init_file, "r") as f1:
        #dr = [elem for elem in DictReader(f1)]
        dr = []
        for elem in DictReader(f1):
            elem = {x.replace(' ', ''): v for x, v in elem.items()}
            elem = {x: v.replace(' ', '') for x, v in elem.items() if type(v)==str}
            dr.append(elem)

    for elem in dr:
        rooms.append(Room(name_take3=elem['Take3Name'],
                          name_hotel=elem['HotelName'],
                          number=elem['Number'],
                          )
                    )
    list(map(lambda x: x.save(), rooms))


def create_rooms_main(init_file =""):
    dr = None
    # {hotel_name: take3_name}
    type_mapping = [
           {"Hearing Accessible King": "Standard Room (1 King Bed)"},
           {"Queen": "Standard Room (2 Queen Beds)"},
           {"Executive Suite": "Knew Management Suite (1 King Bed)"},
           {"Accessible Queen": "Standard Room (2 Queen Beds)"},
           {"Hearing Accessible Queen": "Standard Room (2 Queen Beds)"},
           {"King": "Standard Room (1 King Bed)"},
           {"Smoking Executive Suite": "Knew Management Suite (1 King Bed)"},
           {"Smoking Queen": "Standard Room (2 Queen Beds)"},
           {"Smoking King": "Standard Room (1 King Bed)"},
           {"Smoking Accessible Queen": "Standard Room (2 Queen Beds)"},
           {"Lakeview King": "Lakeview Standard Room (1 King Bed)"},
           {"Lakeview Queen": "Lakeview Standard Room (2 Queen Beds)"},
           {"Accessible King": "Standard Room (1 King Bed)"},
           {"2 Queen Accessible Sierra Suite": "Babyface Suite (2 Queen Beds)"},
           {"2 Queen Sierra Suite": "Babyface Suite (2 Queen Beds)"},
           {"Wedding Office": "IGNORE"},
           {"Chapel": "IGNORE"},
           {"1 King Sierra Suite": "Babyface Suite (1 King Bed)"},
           {"Lakeview 1 King Sierra Suite": "Babyface Suite (1 King Bed)"},
           {"Accessible 1 King Lakeview Sierra Suite": "Babyface Suite (1 King Bed)"},
           {"Tahoe Suite": "Clavae Suite (1 King Bed)"},
           {"Smoking 1 King Sierra Suite": "Babyface Suite (1 King Bed)"},
           {"Smoking Tahoe Suite": "Clavae Suite (1 King Bed)"},
           {"Smoking 2 Queen Sierra Suite": "Babyface Suite (2 Queen Beds)"},
           {"Smoking Lakeview Queen": "Lakeview Standard Room (2 Queen Beds)"},
    ]
    rooms=[]
    with open(init_file, "r") as f1:
        dr = [elem for elem in DictReader(f1)]
    for elem in dr:
        #TODO(tb): omg this is big O off the charts. make it more efficient
        for name in type_mapping:
            if(elem["Room Type"] in name.keys()):
                #print(f'[+] Adding room to inventory: {elem["Room Type"]}')
                take3_name = name[elem["Room Type"]]

        if(elem["ROOMBAHT"]=="R"):
            rooms.append(Room(name_hotel=elem['Room Type'].lstrip(),
                             number=elem['Room'].lstrip(),
                             available=True,
                             name_take3=take3_name
                             )
                       )
        else:
            print(f'[-] Room excluded by ROOMBAHT colum: {elem}')
        #print(f"room: {rooms[len(rooms)-1].available}")

    print(f'swappable rooms: {rooms}')
    list(map(lambda x: x.save(), rooms))


def create_admins(init_file=None):
    dr = None
    with open(init_file, "r") as f1:
        dr = []
        for elem in DictReader(f1):
            dr.append(elem)
    for admin_new in dr:
        print(f"[+] Creating admin: {admin_new['name']}, {admin_new['email']}, {admin_new['is_admin']}")
        staff=Staff(name=admin_new['name'],
            email=admin_new['email'],
            is_admin=admin_new['is_admin'])
        staff.save()
    
        characters = string.ascii_letters + string.digits + string.punctuation
        otp = ''.join(random.choice(characters) for i in range(10))
        print(f"[+] Created new admin Email {admin_new['email']} Admin {otp}")
        if(SEND_MAIL):
            print(f'[+] Sending invite for guest {guest_new["first_name"]} {guest_new["last_name"]}')
    
            body_text = f"""
                Email {admin_new['email']}
                Admin {otp}
                
                Good Luck, Starfighter.
                
            """
            send_mail("RoomService RoomBaht",
                      body_text,
                      "placement@take3presents.com",
                      [guest_new["email"]],
                      auth_user="placement@take3presents.com",
                      auth_password=os.environ['EMAIL_HOST_PASSWORD'],
                      fail_silently=False,)



RANDOM_ROOMS = True
SEND_MAIL = False 
def main():
    """ This is oldy timey and dodge AF. put some switches on this thing. """

    Room.objects.all().delete()
    create_rooms_main(init_file='../samples/exampleMainRoomList.csv')


    Staff.objects.all().delete()
    create_admins(init_file="../samples/exampleMainAdminList.csv")





if __name__=="__main__":
    main()
