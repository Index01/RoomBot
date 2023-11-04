from django.core.management.base import BaseCommand, CommandError
from reservations.models import Room, Guest

class Command(BaseCommand):
    help = "unfuck half baked swaps"

    def handle(self, *args, **kwargs):
        rooms = Room.objects.all()
        for room in rooms:
            msg = ''

            # side effect of swap drama.
            if room.guest and room.number != room.guest.room_number:
                msg = f"    Room number {room.number} / guest room number {room.guest.room_number}\n"

            if room.guest and room.primary != room.guest.name:
                msg = f"{msg}    Room primary {room.primary} / guest name {room.guest.name}\n"

            # side effect of transferring placed rooms
            if room.sp_ticket_id:
                guest = None
                alt_msg = ''
                try:
                    guest = Guest.objects.get(ticket=room.sp_ticket_id)
                    if room.number != guest.room_number:
                        alt_msg = f"{alt_msg}    SP Ticket {room.sp_ticket_id} room number {room.number} / guest room number {guest.room_number}\n"

                    if room.primary != guest.name:
                        alt_msg = f"{alt_msg}    SP Ticket {room.sp_ticket_id} primary {room.primary} / guest name {guest.name}"

                except Guest.DoesNotExist:
                    msg = f"{msg}    SP Ticket {room.sp_ticket_id} original owner not found??\n"

                if room.guest is None:
                    print(f"Room {room.number} {room.primary} sp_ticket_id {room.sp_ticket_id} but no guest. Missing / corrupt guests import?\n")
                    continue

                if room.number != guest.room_number \
                   and room.primary != guest.name \
                       and guest is not None:
                    try:
                        guest = Guest.objects.get(transfer=room.sp_ticket_id)
                        if room.number != guest.room_number:
                            msg = f"{msg}    SP Ticket {room.sp_ticket_id} transfer {guest.ticket} room number {room.number} / guest room number {guest.room_number}\n"

                        if room.primary != guest.name:
                            msg = f"{msg}    SP Ticket {room.sp_ticket_id} transfer {guest.ticket} primary {room.primary} / guest name {guest.name}\n"

                        if room.primary == guest.name and \
                           room.number == guest.room_number:
                            msg = f"{msg}   SP Ticket {room.sp_ticket_id} transfer {guest.ticket} guest name {guest.name} guest room number {guest.room_number}\n"

                    except Guest.DoesNotExist:
                        msg = f"{msg}    SP Ticket {room.sp_ticket_id} transfer owner not found??\n{alt_msg}"

            # general corruption which could bubble up during orm/sql manipulation
            if room.sp_ticket_id and room.is_comp:
                msg = f"{msg}    SP Ticket {room.sp_ticket_id} on comp'd room {room.name_hotel} {room.number}\n"

            if room.check_in is None:
                msg = f"{msg}    Room {room.name_hotel} {room.number} has blank check_in date"

            if room.check_out is None:
                msg = f"{msg}    Room {room.name_hotel} {room.number} has blank check_out date"

            if len(msg) > 0:
                print(f"Room {room.number} Mismatch!\n{room.hotel_sku()} - art:{room.is_art} comp:{room.is_comp} placed:{room.is_placed}\n{msg}")
