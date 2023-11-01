from django.core.management.base import BaseCommand, CommandError
from reservations.models import Room
from reservations.helpers import real_date

class Command(BaseCommand):
    help = "Edit aspects of a room"
    def add_arguments(self, parser):
        parser.add_argument('number',
                            help='The room number')
        parser.add_argument('--primary',
                            help='Specify primary name (blank string to remove)')
        parser.add_argument('--secondary',
                            help='Specify secondary name (blank string to remove)')

        parser.add_argument('--check-in',
                            help='Specify check-in date (MM/DD, blank string to remove)')

        parser.add_argument('--check-out',
                            help='Specify check-out date (MM/DD, blank string to remove)')

        parser.add_argument('--notes',
                            help='Specify room notes (blank string to remove')

        parser.add_argument('--guest-notes',
                            help='Specify guest notes (blank string to remove')

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

    def handle(self, *args, **kwargs):
        if 'number' not in kwargs:
            raise CommandError("Must specify room number")

        if kwargs['swappable'] and kwargs['not_swappable']:
            raise CommandError("Cannot specify both --swappable and --not-swappable")

        hotel_name = None
        if kwargs['hotel_name'].lower() == 'ballys':
            hotel_name = 'Ballys'
        elif kwargs['hotel_name'].lower() == 'hard rock' or \
           kwargs['hotel_name'].lower() == 'hardrock':
            hotel_name = 'Hard Rock'
        else:
            raise CommandError(f"Invalid hotel {kwargs['hotel_name']} specified")

        room = None
        try:
            room = Room.objects.get(number=kwargs['number'])
        except Room.ObjectNotFound as exp:
            raise CommandError(f"Room {kwargs['number']} not found") from exp

        room_changed = False
        if kwargs['primary'] is not None and kwargs['primary'] != room.primary:
            room.primary = kwargs['primary'].title()
            room_changed = True

        if kwargs['secondary'] is not None and kwargs['secondary'] != room.secondary:
            room.secondary = kwargs['secondary'].title()
            room_changed = True

        if kwargs['check_in'] is not None:
            if kwargs['check_in'] != '':
                real_check_in = real_date(kwargs['check_in'])
                if real_check_in != room.check_in:
                    room.check_in = real_check_in
                    room_changed = True

            elif kwargs['check_in'] == '' and room.check_in is not None:
                room.check_in = None
                room_changed = True

        if kwargs['check_out'] is not None:
            if kwargs['check_out'] != '':
                real_check_out = real_date(kwargs['check_out'])
                if real_check_out != room.check_out:
                    room.check_out = real_check_out
                    room_changed = True

            elif kwargs['check_out'] == '' and room.check_out is not None:
                room.check_out = None
                room_changed = True

        if kwargs['notes'] is not None and kwargs['notes'] != room.notes:
            room.notes = kwargs['notes']
            room_changed = True

        if kwargs['guest_notes'] is not None and kwargs['guest_notes'] != room.guest_notes:
            room.guest_notes = kwargs['guest_notes']
            room_changed = True

        if kwargs['swappable'] and not room.is_swappable:
            room.is_swappable = True
            room_changed = True
        elif kwargs['not_swappable'] and room.is_swappable:
            room.is_swappable = False
            room_changed = True

        if room_changed:
            self.stdout.write('Updated room')
            room.save()
