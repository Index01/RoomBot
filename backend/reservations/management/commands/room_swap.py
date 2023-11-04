from django.core.management.base import BaseCommand, CommandError
from reservations.models import Room, SwapError

class Command(BaseCommand):
    help = "Manually swap a room"
    def add_arguments(self, parser):
        parser.add_argument('room_one',
                            help='The first room in The Arrangement')
        parser.add_argument('room_two',
                            help='The second room in The Arrangement')
        parser.add_argument('--hotel_one',
                            help='The hotel the first room is associated with. Defaults to Ballys.',
                            default='Ballys')
        parser.add_argument('--hotel_two',
                            help='The hotel the second room is associated with. Defaults to Ballys.',
                            default='Ballys')

    def handle(self, *args, **kwargs):
        if 'room_one' not in kwargs or 'room_two' not in kwargs:
            raise CommandError('must specify two rooms to swap')

        room_one = None
        room_two = None

        try:
            room_one = Room.objects.get(number=kwargs['room_one'], name_hotel=kwargs['hotel_one'])
        except Room.DoesNotExist:
            raise CommandError(f"room {kwargs['hotel_one']} {kwargs['room_one']} does not exist") from Room.DoesNotExist

        try:
            room_two = Room.objects.get(number=kwargs['room_two'], name_hotel=kwargs['hotel_two'])
        except Room.DoesNotExist:
            raise CommandError(f"room {kwargs['hotel_two']} {kwargs['room_two']} does not exist") from Room.DoesNotExist

        if not room_one.swappable():
            raise CommandError(f"room {kwargs['hotel_one']} {kwargs['room_one']} is not swappable")

        if not room_two.swappable():
            raise CommandError(f"room {kwargs['hotel_two']} {kwargs['room_two']} is not swappable")

        try:
            Room.swap(room_one, room_two)
        except SwapError as exp:
            raise CommandError(f"Unable to swap room {exp.msg}") from exp

        self.stdout.write(f"Swapped {kwargs['hotel_one']} {kwargs['room_one']} and {kwargs['hotel_two']} {kwargs['room_two']}")
