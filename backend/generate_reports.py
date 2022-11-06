

import django
django.setup()
from csv import DictReader, DictWriter
from reservations.models import Guest, Room
from django.core.mail import EmailMessage, get_connection
from django.forms.models import model_to_dict


#secpty_export = "../samples/main_guest_list_11042022.csv"
secpty_export = "directed_fixed.csv"
ticket_file = "../samples/verify_output.csv"

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


def dump_guest_rooms():
    guests = Guest.objects.all()
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

dump_guest_rooms()

bod = "Diff dump, roombaht http logs, reservations script log"
#bod = f"secpty num lines: {len(secpty_lines)} verified lines from placed+excluded: {len(ticket_lines)}"
conn = get_connection()
msg = EmailMessage(subject="RoomBaht Logging", 
                   body=bod, 
                   to=["jessica.nan.goldstein@gmail.com", "jeff@take3presents.com", "tyler32bit@gmail.com"],
                   connection=conn)
msg.attach_file(secpty_export)
msg.attach_file('../output/diff_dump.md')
msg.attach_file('../output/roombaht_application.md')
msg.attach_file('../output/log_script_out.md')
msg.attach_file('../output/guest_dump.csv')
msg.attach_file('../output/room_dump.csv')

msg.send()

