
import os
import random
import string
import django
django.setup()
from reservations.models import Guest, Room
from django.core.mail import send_mail
from django.core.mail import EmailMessage, get_connection
from django.forms.models import model_to_dict
from csv import DictReader, DictWriter
import time

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


def search_ticket(ticket, guest_entries):
    while(len(guest_entries)>0):
        guest = guest_entries.pop()
        print(f'guest.ticket: {guest.ticket}, ticket: {ticket}')
        if(guest.ticket == ticket):
            return True
        else:
            continue
    return False


def assign_room(type_purchased):
        if (RANDOM_ROOMS):
            rooms = Room.objects.all()
            no_guest=list(filter(lambda x:x.guest==None, rooms))
            for room in no_guest:
                #print(f'attempting: {room.name_take3} and {type_purchased}')
                if(room.name_take3==type_purchased or room.name_hotel==type_purchased):
                    print(f"[+] Assigned room number: {room.number}")
                    return room
                else:
                    pass
            print(f'[-] No room of matching type available. looking for: {type_purchased} remainging inventory:\nTake3names: {[elem.name_take3 for elem in no_guest]}\nHotel names: {[elem.name_hotel for elem in no_guest]}')
            return None
        else:
            # testing purposes
            print(f'test room assigned in create')
            return Room(number=666)


def guest_contact_new(guest_new, otp):
    ''' Create guest send email '''
    print(f"[+] Creating guest: {guest_new['first_name']} {guest_new['last_name']}, {guest_new['email']}, {guest_new['ticket_code']}")
    existing_ticket = Guest.objects.filter(ticket=guest_new["ticket_code"])
    # verify ticket does not exist
    if(len(existing_ticket)==0):
        room = assign_room(guest_new["product"])
        if(room is None):
            return

        guest=Guest(name=guest_new['first_name']+" "+guest_new['last_name'],
            email=guest_new['email'],
            ticket=guest_new['ticket_code'],
            jwt=otp,
            room_number=room.number)
        guest.save()

        room.guest=guest
        room.save()

    time.sleep(5)
    if(SEND_MAIL):
        print(f'[+] Sending invite for guest {guest_new["first_name"]} {guest_new["last_name"]}')

        body_text = f"""
BleepBloopBleep, this is the Room Service RoomBaht for Room Swaps letting you know the floors have been cleaned and you have been assigned a room. No bucket or mop needed.

After you login below you can view your current room, look at other rooms and send trade requests. This functionality is only available until Monday 11/7 at 5pm PST, so please make sure you are good with what you have or trade early.

Goes without saying, but don't forward this email.

This is your password, there are many like it but this one is yours. Once you use this password on a device, RoomBaht will remember you, but only on that device.
Copy and paste this password. Because let’s face it, no one should trust humans to make passwords:
{otp}
http://ec2-3-21-92-196.us-east-2.compute.amazonaws.com:3000/login

Good Luck, Starfighter.

        """

        send_mail("RoomService RoomBaht",
                  body_text,
                  "placement@take3presents.com",
                  [guest_new["email"]],
                  auth_user="placement@take3presents.com",
                  auth_password=os.environ['EMAIL_HOST_PASSWORD'],
                  fail_silently=False,)


def guest_contact_exists(guest_new, otp):
    ''' Get the ticket numbers
        if ticket exists copy associated room number and delete the existing entry.
        create new entry with existing room number or new room num is none previously existed.
    '''
    print(f"[+] Guest exists, creating ticket {guest_new['email']} ticket: {guest_new['ticket_code']}")
    room = assign_room(guest_new["product"])
    if(room is None):
        return

    guest=Guest(name=guest_new['first_name']+" "+guest_new['last_name'],
        email=guest_new['email'],
        ticket=guest_new['ticket_code'],
        jwt=otp,
        room_number=room.number)

    guest.save()
    room.guest=guest
    print(f"[+] Assigned room number: {room.number}")
    room.save()

def guest_owner_update(guest_new, otp):
    '''  Email exists and Ticket exists. If existing guest does not match new guest, update existing entry.'''
    existing_ticket = Guest.objects.filter(ticket=guest_new["ticket_code"])
    room_num = existing_ticket[0].room_number
    if(guest_new["email"]!=existing_ticket[0].email):
        print(f'[-] Update detected')
        print(f"existing: {existing_ticket}, fields: {existing_ticket[0].name},{existing_ticket[0].ticket},{existing_ticket[0].room_number}")
        existing_ticket.update(
                              name=guest_new['first_name']+" "+ guest_new['last_name'],
                              email=guest_new['email'],
                              ticket=guest_new['ticket_code'],
                              jwt=otp,
                              room_number = room_num)


        print(f"updated: {existing_ticket}, fields: {existing_ticket[0].name},{existing_ticket[0].ticket},{existing_ticket[0].room_number}")

    else:
        print(f'[*] Email exists, ticket exists, room exists, everything matches entry')


def create_guests(init_file="", init_rooms=""):
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
            #elem = {x.replace(' ', ''): v for x, v in elem.items()}
            #elem = {x: v.replace(' ', '') for x, v in elem.items() if type(v)==str}
            dr.append(elem)
    with open(init_rooms, 'r') as f2:
        black_list = [elem['Ticket ID in SecretParty'] for elem in DictReader(f2) if elem['Ticket ID in SecretParty']!=""]
    print(f"blacklistL {black_list}")

    characters = string.ascii_letters + string.digits + string.punctuation

    for guest_new in dr:
        guest_entries = Guest.objects.filter(email=guest_new["email"])
        if ("Directed Sale Room (1 King Bed)" in guest_new["product"]):
            guest_new["product"] = "King"
        if ("Directed Sale Room (1 Queen Bed)" in guest_new["product"]):
            guest_new["product"] = "Queen"

        #if("Directed Sale Room (2 Queen Beds)"):
        #    guest_new["product"] = "Standard Room (2 Queen Beds)"
        #if("Direct Sale Room (1 King Bed)"):
        #    guest_new["product"] = "Standard Room (1 King Bed)"
        #if("Standard Room (2 Queen Bed)"):
        #    guest_new["product"] = "Standard Room (2 Queen Beds)"

        if ("Hard Rock" in guest_new["product"]):
            continue
        if (guest_new['ticket_code'] in black_list):
            print(f'[-] Ticket {guest_new["ticket_code"]} {guest_new["first_name"]} {guest_new["last_name"]} excluded by rooms csv column P')
            continue

        # If email doesnt exist, send email and create guest
        if (guest_search(gl, 0, glen, guest_new["email"])==None and len(guest_entries)==0):
            print(f'Email doesnt exist. Creating new guest contact.')
            otp = ''.join(random.choice(characters) for i in range(10))
            guest_contact_new(guest_new, otp)
            continue

        # If email does exist. check whether ticket exists. if not, create guest
        if(len(Guest.objects.filter(ticket=guest_new["ticket_code"]))==0):
            otp = ''.join(random.choice(characters) for i in range(10))
            guest_contact_exists(guest_new, otp)

        # If email does exist. check whether ticket exists. if so, update the guest entry.
        # This case if for resigning room/tickets to new owner. update operation so secret party export is source of authority.
        elif(len(Guest.objects.filter(ticket=guest_new["ticket_code"]))!=0):
            otp = ''.join(random.choice(characters) for i in range(10))
            guest_owner_update(guest_new, otp)




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

           #{"Direct Sale Room (1 King Bed)}": "Standard Room (1 King Bed)"},
           #{"Directed Sale Room (2 Queen Beds)": "Standard Room (2 Queen Bed)"},

           #{"Queen": "Directed Sale Room (2 Queen Beds)"},
           #{"King": "Direct Sale Room (1 King Bed)"},
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




RANDOM_ROOMS = True
SEND_MAIL = False
def main():
    """ This is oldy timey and dodge AF. put some switches on this thing. """

    #Room.objects.all().delete()
    #create_rooms()


    #create_rooms_main(init_file='../samples/main_room_list_11042022.csv')


    #Guest.objects.all().delete()
    create_guests(init_file="../samples/secretPartyExmple_swag.csv",
                  init_rooms="../samples/roomsExample_swag.csv")
    #create_guests(init_file="../samples/secretPartyExmple_swag.csv", init_rooms="../samples/main_room_list_11042022.csv")
    #create_guests(init_file="../samples/main_guest_list_11022022.csv", init_rooms="../samples/main_room_list_11042022.csv")
    #create_guests(init_file="./directed_fixed_test.csv", init_rooms="../samples/main_room_list_11042022.csv")


    #create_guests(init_file="./directed_fixed.csv", init_rooms="../samples/main_room_list_11042022.csv")


    # Testing, air-quotes
    #print(f'--------Omg this is terrible but here is how we will verify stuff-------')
    #print(f"Swap test, csv update everything is same except 2 guests trade tickets:")
    #create_guests(init_file="../samples/secretPartyExmple_swapTickets_swag.csv", init_rooms="../samples/main_room_list_11042022.csv")


    # logging, air quotes
    #dump_guest_rooms()




if __name__=="__main__":
    main()
