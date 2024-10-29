from django.core.management.base import BaseCommand, CommandError
from reservations.models import Room
from reservations.management import getch
import reservations.config as roombaht_config

class Command(BaseCommand):
    help = "Edit aspects of a room"
    def add_arguments(self, parser):
        parser.add_argument('number',
                            help='The room number')
        parser.add_argument('--add-name',
                            help='Name to add to room')
        parser.add_argument('--remove-name',
                            help='Name to remove from room')
        parser.add_argument('--check-in',
                            help='Specify check-in date (MM/DD, blank string to remove)')

        parser.add_argument('--check-out',
                            help='Specify check-out date (MM/DD, blank string to remove)')

        parser.add_argument('--hotel-name',
                            default='Ballys',
                            help='The hotel name. Defaults to Ballys.')

        # there is a better way to do this kind of arg but we cannot assume how the room is set
        parser.add_argument('--swappable',
                            help='Marks a room as swappable',
                            default=False,
                            action='store_true')

        parser.add_argument('--not-swappable',
                            help='Marks a room as not swappable',
                            default=False,
                            action='store_true')

        parser.add_argument('--placed',
                            help='Marks a room as placed',
                            default=False,
                            action='store_true')

        parser.add_argument('--not-placed',
                            help='Marks a room as not placed',
                            default=False,
                            action='store_true')

        parser.add_argument('--comp',
                            help='Marks a room as comp',
                            default=False,
                            action='store_true')

        parser.add_argument('--not-comp',
                            help='Marks a room as not comp',
                            default=False,
                            action='store_true')

        parser.add_argument('--unassign',
                            help='Unassign the room. Annoying to undo',
                            default=False,
                            action='store_true')

        parser.add_argument('--reset-swap',
                            help='Resets last swap time and any pending swap code',
                            default=False,
                            action='store_true')

    def handle(self, *args, **kwargs):
        if 'number' not in kwargs:
            raise CommandError("Must specify room number")

        if kwargs['swappable'] and kwargs['not_swappable']:
            raise CommandError("Cannot specify both --swappable and --not-swappable")

        hotel = kwargs['hotel_name'].title()
        if hotel not in roombaht_config.GUEST_HOTELS:
            raise CommandError(f"Invalid hotel {kwargs['hotel_name']} specified")

        room = None
        try:
            room = Room.objects.get(number=kwargs['number'], name_hotel=hotel)
        except Room.ObjectNotFound as exp:
            raise CommandError(f"Room {kwargs['number']} not found") from exp

        if kwargs['unassign']:
            if kwargs['swappable'] \
               or kwargs['not_swappable'] \
               or kwargs['names']:
                raise CommandError('do not specify other args when unassigning room')

        if kwargs['unassign']:
            self.stdout.write((
                f"Are you sure you want to unassign {room.name_hotel} {room.number}?\n"
                f"It will be super annoying to undo this\n"
                f"[y/n]"))
            if getch().lower() != 'y':
                raise CommandError('user said nope')

            room.guest = None
            room.names = ''
            room.is_available = True
            room.is_swappable = True
            room.save()
            self.stdout.write("Unassigned room")
            return

        if kwargs['add_name'] is not None and \
           not room.resident(kwargs['add_name']):
            room.resident_add(kwargs['add_name'])

        if kwargs['remove_name'] is not None and \
           room.resident(kwargs['remove_name']):
            room.resident_remove(kwargs['remove_name'])

        if kwargs['check_in'] is not None:
            room.check_in = kwargs['check_in']

        if kwargs['check_out'] is not None:
            room.check_out = kwargs['check_out']

        if kwargs['swappable'] and not room.is_swappable:
            room.is_swappable = True
        elif kwargs['not_swappable'] and room.is_swappable:
            room.is_swappable = False

        if kwargs['placed'] and not room.is_placed:
            room.is_placed = True
        elif kwargs['not_placed'] and room.is_placed:
            room.is_placed = False

        if kwargs['reset_swap']:
            room.swap_time = None
            room.swap_code = None

        if room.is_dirty():
            self.stdout.write(f"Updated room: {kwargs['number']}")
            room.save_dirty_fields()
