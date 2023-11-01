from django.core.management.base import BaseCommand, CommandError
from reservations.models import Room

class Command(BaseCommand):
    help = "Show information on a room"
    def add_arguments(self, parser):
        parser.add_argument('number',
                            help='The room number')

    def handle(self, *args, **kwargs):
        if 'number' not in kwargs:
            raise CommandError("Must specify room number")

        room = None
        try:
            room = Room.objects.get(number=kwargs['number'])
        except Room.ObjectNotFound as exp:
            raise CommandError(f"Room {kwargs['number']} not found") from exp

        desc = f"{room.hotel_sku()} in {room.name_hotel}"
        if room.guest:
            desc = f"{desc} owned by {room.guest.email}"

        if room.primary:
            desc = f"{desc}\n   primary resident: {room.primary}"
            if room.secondary:
                desc = f"{desc}, secondary resident: {room.secondary}"

        flags = []
        if room.is_available:
            flags.append('available')

        if room.is_swappable:
            flags.append('swappable')

        if room.is_art:
            flags.append('art room')

        if room.is_comp:
            flags.append('comped')

        if room.is_placed:
            flags.append('placed')

        if room.placed_by_roombot:
            flags.append('roombaht')

        if room.is_special:
            flags.append('special')

        details = ''
        if len(flags) > 0:
            details = f"{details} Flags: {','.join(flags)}"

        if room.check_in:
            details = f"{details} Check-in: {room.check_in}"
        else:
            details = f"{details} Check-in: Unknown"

        if room.check_out:
            details = f"{details} Check-out: {room.check_out}"
        else:
            details = f"{details} Check-out: Unknown"

        self.stdout.write(desc)
        self.stdout.write(details)

        if room.notes:
            self.stdout.write(f"Room notes: {room.notes}")

        if room.guest_notes:
            self.stdout.write(f"Guest notes: {room.guest_notes}")
