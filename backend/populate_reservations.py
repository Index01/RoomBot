
import os 
import random
import string
import boto3
import django
import pandas as pd
django.setup()
from reservations.models import Guest, Room
from django.core.mail import send_mail
from csv import DictReader

def guest_sort(guest_list):
    '''
        merge sort by email. u know wat time it is
    '''
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
    '''
        binary search by email
    ''' 
    if high >= low:
        mid = (high + low) // 2
        #print(f'arr mid: {arr[mid].email }')
        if arr[mid].email == x:
            #print(f'returning: {arr[mid]}')
            return arr[mid]
        elif arr[mid].email > x:
            return guest_search(arr, low, mid - 1, x)
        else:
            return guest_search(arr, mid + 1, high, x)
    else:
        return None

def send_plain_email():
    ses_client = boto3.client("ses", region_name="us-west-2")
    CHARSET = "UTF-8"
    
    response = ses_client.send_email(
    Destination={
        "ToAddresses": [
        "tyler32bit@gmail.com",
        ],
    },
    Message={
        "Body": {
            "Text": {
                "Charset": CHARSET,
                "Data": "Hello, world!",
            }
        },
    "Subject": {
        "Charset": CHARSET,
        "Data": "RoomBot SeS test",
        },
    },
    Source="t4l3rb@gmail.com",
    )

def search_ticket(ticket, guest_entries):
    while(len(guest_entries)>0):
        guest = guest_entries.pop()
        if(guest.ticket == ticket):
            return True
        else:
            continue
    return False

#
#    try:
#        guest = guest_entries.pop()
#    except IndexError as e:
#        print("New ticket")
#        return False
#    if(guest.ticket == ticket):
#        print("found ticket")
#        return True
#    else:
#        search_ticket(ticket, guest_entries)
#    return False
#

def create_guests(init_file="../samples/secretPartyExmple_swag.csv"): 
    dr = None
    new_guests=[]
    gl = list(Guest.objects.all())
    guest_sort(gl)
    try:
        glen = len(gl)-1
    except TypeError as e:
        print(f"No existing guests to show ")
        glen=0
    with open(init_file, "r") as f1:
        dr = []
        for elem in DictReader(f1):
            elem = {x.replace(' ', ''): v for x, v in elem.items()}
            elem = {x: v.replace(' ', '') for x, v in elem.items() if type(v)==str}
            dr.append(elem)
    characters = string.ascii_letters + string.digits + string.punctuation
    otp = ''.join(random.choice(characters) for i in range(8))

    for guest_new in dr:
        guest_entries = Guest.objects.filter(email=guest_new["Email"])
        # If email doesnt exist, send email and create guest
        if (guest_search(gl, 0, glen, guest_new["Email"])==None and len(guest_entries)==0):
            print(f"[+] Sending invite and creating guest: {guest_new}")
            guest=Guest(name=guest_new['Name'], 
                email=guest_new['Email'], 
                ticket=guest_new['Ticket'], 
                jwt=otp,
                invitation=guest_new['Invitation'])
            guest.save()

            if (RANDOM_ROOMS):
                rooms = Room.objects.all()
                no_guest=list(filter(lambda x:x.guest==None, rooms))
                try:
                    room = no_guest.pop()
                except IndexError as e:
                    print(f'No rooms available')
                room.guest=guest
                print(f"[+] Assigned room number: {room.number}")
                room.save()
            
            body_text = f"Well BleepBloopBleep, this is the RoomService RoomBaht letting you know the floors have been cleaned and you have been assigned a room. No bucket or mop needed.\n\nAt RoomService rooms are randomly assigned. But you want that super premo crib 20 steps closer to the ice machine, right? Well now you can look at some maps, find someone with a comparable room and ask them if they wanna swap rooms. Rooms can only be swapped with the same room type, if you want to upgrade, downgrade, sidegrade or any other kind of grade, go sell your thing and get what you want then swap. After changing rooms you must checkin at the front desk and handle the financials. \n\nCopy and paste this one time password. Because lets face it, no one trusts humans to make passwords:\n{otp} \nhttp://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:3000/login\n\nGood Luck, Starfighter."
            
            send_mail("[TESTING]RoomService RoomBaht", 
                      body_text,
                      "t4l3rb@gmail.com", 
                      [guest_new["Email"]],
                      fail_silently=False,)
            continue

        # If email does exist. check whether ticket exists. if not, create guest
        if (search_ticket(guest_new["Ticket"], list(guest_entries))==False):
            print(f"[+] Guest exists, creating ticket {guest_new['Email']} ticket: {guest_new['Ticket']}")
            guest=Guest(name=guest_new['Name'], 
                email=guest_new['Email'], 
                ticket=guest_new['Ticket'], 
                jwt=otp,
                invitation=guest_new['Invitation'])
            guest.save()
        if (RANDOM_ROOMS):
            rooms = Room.objects.all()
            no_guest=list(filter(lambda x:x.guest==None, rooms))
            try:
                room = no_guest.pop()
            except IndexError as e:
                print(f'No rooms available')
            room.guest=guest
            print(f"[+] Assigned room number: {room.number}")
            room.save()


def create_rooms(init_file ="../samples/roomsExample_swag.csv"):
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

def create_rooms_main(init_file ="../samples/main_room_list_10262022.csv"):
    dr = None
    rooms=[]
    with open(init_file, "r") as f1:
        dr = [elem for elem in DictReader(f1)]
    for elem in dr:
        if (elem["Changeable"] == "Y"):
            print(f"swappable: {elem}")
            if(elem["First Name"]==""):
                swappable = False
            else:
                swappable = True
            rooms.append(Room(name_hotel=elem['Room Type'].lstrip(),
                             number=elem['Room'].lstrip(),
                             available=swappable,
                             )
                       )
            print(f"room: {rooms[len(rooms)-1].available}")

    list(map(lambda x: x.save(), rooms))




RANDOM_ROOMS = True
def main():
    #this os env is needed but no wants to set. set through term
    os.environ["DJANGO_SETTINGS_MODULE"]='reservations.settings'

    Room.objects.all().delete()
    create_rooms_main()

    Guest.objects.all().delete()
    create_guests()



if __name__=="__main__":
    main()
