
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
    
        print(f"[+] Created staff: {staff_new['name']}, {staff_new['email']}, otp: {otp}, isadmin: {staff_new['is_admin']}")
        if(SEND_MAIL=="True"):
            print(f'[+] Sending invite for staff member {staff_new["email"]}')
    
            body_text = f"""
                Congratulations, u have been deemed Staff worthy material.

                Email {staff_new['email']}
                Admin {otp}
                
                login at blahblahblah/login  
                then go to blahblahbla/admin
                Good Luck, Starfighter.
                
            """
            send_mail("RoomService RoomBaht",
                      body_text,
                      "placement@take3presents.com",
                      [guest_new["email"]],
                      auth_user="placement@take3presents.com",
                      auth_password=os.environ['EMAIL_HOST_PASSWORD'],
                      fail_silently=False,)



SEND_MAIL = os.environ['ROOMBAHT_SEND_MAIL']
def main():

    Room.objects.all().delete()
    create_rooms_main(init_file='../samples/exampleMainRoomList.csv')


    Staff.objects.all().delete()
    create_staff(init_file="../samples/exampleMainStaffList.csv")





if __name__=="__main__":
    main()
