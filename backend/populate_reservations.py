
import os 
import random
import string
import django
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
        if arr[mid].email == x:
            return mid
        elif arr[mid].email > x:
            return guest_search(arr, low, mid - 1, x)
        else:
            return guest_search(arr, mid + 1, high, x)
    else:
        return None


def create_guests(init_file="../samples/secretPartyExmple_swag.csv"): 
    dr = None
    new_guests=[]
    gl = list(Guest.objects.all())
    guest_sort(gl)
    try:
        glen = len(gl)-1
    except TypeError as e:
        print(f"No existing guests to show ")
    with open(init_file, "r") as f1:
        dr = [elem for elem in DictReader(f1)]

    characters = string.ascii_letters + string.digits + string.punctuation
    otp = ''.join(random.choice(characters) for i in range(8))

    for elem in dr:
        print(f"[+] Sending invite and creating guest: {elem}")
        if (guest_search(gl, 0, glen, elem[" Email"])):
            send_mail("RoomService RoomSelekta", 
                    f"Here is your sweet RoomService RoomSelekta link, brah. \n http://127.0.0.1:3000/login\n Copy and paste this one time password. B/c lets face it, noone trusts humans to make passwords. \n OTP: {otp}", 
                      "t4l3rb@gmail.com", 
                      [elem[" Email"]])
        else:
            print(elem[' Email'].lstrip())
            new_guests.append(Guest(name=elem[' Name'].lstrip(), 
                                 email=elem[' Email'].lstrip(), 
                                 ticket=elem['Ticket'].lstrip(), 
                                 jwt=otp,
                                 invitation=elem[' Invitation'].lstrip()))
    list(map(lambda x: x.save(), new_guests))


def create_rooms(init_file ="../samples/roomsExample_swag.csv"):
    dr = None
    rooms=[]
    with open(init_file, "r") as f1:
        dr = [elem for elem in DictReader(f1)]
    for elem in dr:
        rooms.append(Room(name_take3=elem['Take3Name'].lstrip(), 
                          name_hotel=elem[' HotelName'].lstrip(), 
                          number=elem[' Number'].lstrip(), 
                          )
                    )
    list(map(lambda x: x.save(), rooms))





def main():
    #this os env is needed but no wants to set. set through term
    os.environ["DJANGO_SETTINGS_MODULE"]='room_bot.settings'

    create_guests()
    create_rooms()


if __name__=="__main__":
    main()
