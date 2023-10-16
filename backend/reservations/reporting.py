

import django
django.setup()
from csv import DictReader, DictWriter
from reservations.models import Guest, Room
from django.forms.models import model_to_dict


secpty_export = "../samples/exampleMainGuestList.csv"
ticket_file = "../samples/exampleVerifiedTickets.csv"



def read_write_reports():
    secpty_lines = []
    ticket_lines = []
    missing = []
    with open(secpty_export, "r") as f1:
        for elem in DictReader(f1):
            secpty_lines.append(elem)
    
    with open(ticket_file, "r") as f2:
        for elem in DictReader(f2):
            ticket_lines.append(elem)
    
    for line in secpty_lines:
        ticket = line['ticket_code']
        for check_row in ticket_lines:
            if(ticket in check_row['placed'] or ticket in check_row['all_guests']):
                missing.append(f'[+] Ticket Found in both: {line} {check_row}')
                continue
            else:
                continue
            print(f'[-] Ticket not placed or excluded: {line}')
            missing.append(f'[-] Ticket not found {line}')
    
    
    with open('../output/diff_dump.md', 'w') as f3:
        for elem in missing:
            f3.write(f"{elem}\n")

def diff_latest(rows):
    diff_count = 0
    with open('./diff_latest.csv' , 'w') as diffout:
        guests = Guest.objects.all()
        diffout.write("Things in latest guest list upload but not in the db\n")
        for ind, row in enumerate(rows):
            guest_new = row.split(',')
            existing_ticket = Guest.objects.filter(ticket=guest_new[0])
            # ignore the first and last lines. what could go wrong
            if(len(existing_ticket)!=1 and ind!=0 and ind!=len(rows)-1):
                print("diff")
                diff_count+=1
                diffout.write(f'{guest_new[0]},{guest_new[1]},{guest_new[2]},{guest_new[3]}\n')
    
        diffout.write("Things in db but not in most recent guest list upload\n")
        for guest in guests:
            for ind, row in enumerate(rows):
                guest_new = row.split(',')
                if(guest.ticket==guest_new[0]):
                    break
                elif(guest.ticket!=guest_new[0] and ind==len(rows)-1):
                    diff_count+=1
                    print("diff2")
                    diffout.write(f'{guest.ticket},{guest.name},{guest.email}\n')
                else:
                    continue
    return diff_count


def dump_guest_rooms():
    guests = Guest.objects.all()
    print(f'[-] dumping guests and room tables')
    with open('../output/guest_dump.csv', 'w+') as guest_file:
        header = [field.name for field in guests[0]._meta.fields if field.name!="jwt" and field.name!="invitation"]
        writer = DictWriter(guest_file, fieldnames=header)
        writer.writeheader()
        for guest in guests:
            data = model_to_dict(guest, fields=[field.name for field in guest._meta.fields if field.name!="jwt" and field.name!="invitation"])
            writer.writerow(data)

    
    rooms = Room.objects.all()
    with open('../output/room_dump.csv', 'w+') as room_file:
        header = [field.name for field in rooms[0]._meta.fields if field.name!="swap_code" and field.name!="swap_time"]
        writer = DictWriter(room_file, fieldnames=header)
        writer.writeheader()
        for room in rooms:
            data = model_to_dict(room, fields=[field.name for field in room._meta.fields if field.name!="swap_code" and field.name!="swap_time"])
            writer.writerow(data)



