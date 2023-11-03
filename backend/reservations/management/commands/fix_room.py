from django.core.management.base import BaseCommand, CommandError
from reservations.models import Room, Guest
from reservations.management import getch

class Command(BaseCommand):
    help = "Attempt to fix a broken room"
    def add_arguments(self, parser):
        parser.add_argument('number',
                            help='The room number')
        parser.add_argument('--hotel-name',
                            default='Ballys',
                            help='The hotel name. Defaults to Ballys.')

    def handle(self, *args, **kwargs):
        if 'number' not in kwargs:
            raise CommandError("Must specify room number")

        room = None
        hotel = None
        if kwargs['hotel_name'].lower() == 'ballys':
            hotel = 'Ballys'
        elif kwargs['hotel_name'].lower() == 'hard rock' or \
           kwargs['hotel_name'].lower() == 'hardrock':
            hotel = 'Hard Rock'
        else:
            raise CommandError(f"Invalid hotel {kwargs['hotel_name']} specified")

        try:
            room = Room.objects.get(number=kwargs['number'], name_hotel = hotel)
        except Room.ObjectNotFound as exp:
            raise CommandError(f"Room {kwargs['number']} not found") from exp


        # if there is a sp_ticket_id and the guest name/number does not match then
        # we try and find a transfer. if that name/number matches, update sp_ticket_id
        if room.sp_ticket_id:
            guest = None
            try:
                guest = Guest.objects.get(ticket = room.sp_ticket_id)
            except Guest.DoesNotExist:
                raise CommandError(f"Unable to find ticket {room.sp_ticket_id}")

            if room.primary != guest.name and \
               room.number != guest.room_number:
                self.stdout.write(f"sp_ticket_id {room.sp_ticket_id} mismatch primary {room.primary} / guest name {guest.name} / number {room.number} / guest room number {guest.room_number}")
                try:
                    transfer_guest = Guest.objects.get(transfer = room.sp_ticket_id)
                    if room.primary == transfer_guest.name and \
                       room.number == transfer_guest.room_number:
                        self.stdout.write(f"Found transfer {transfer_guest.ticket} that matches room number and name, fix? [y/n]")
                        if getch().lower() == 'y':
                            room.sp_ticket_id = transfer_guest.ticket

                    elif room.primary != transfer_guest.name:
                        raise CommandError(f"Transfer {guest.ticket} mismatch primary {room.primary} guest name {guest.name}")
                    elif room.number != guest.room_numner:
                        raise CommandError(f"Transfer {guest.ticket} mismatch number {room.number} guest room number {guest.room_number}")
                    else:
                        raise CommandError(f"Transfer {guest.ticket} mismatch")

                except Guest.DoesNotExist:
                    raise CommandError(f"Unable to find transfer {room.sp_ticket_id}")


        # side effects of swaps gone wrong
        #  * not transferring data on normal swap
        #  * swap then transfer

        if room.guest:
            if room.number != room.guest.room_number:
                self.stdout.write(f"Number mismatch room number {room.number} / guest room number {room.guest.room_number}. Update guest from room? [y/n]")
                if getch().lower() == 'y':
                    room.guest.room_number = room.number
                    room.guest.save()

            if room.primary != room.guest.name:
                self.stdout.write(f"Name mismatch primary {room.primary} / guest name {room.guest.name}. Update room from guest? [y/n]")
                if getch().lower() == 'y':
                    room.primary = room.guest.name

        if room.is_dirty():
            self.stdout.write(f"Saving room {room.number}")
            room.save_dirty_fields()
        else:
            self.stdout.write(f"Nothing to do for room {room.number}")
