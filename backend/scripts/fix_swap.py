from django.core.management.base import BaseCommand, CommandError
from reservations.models import Room
from reservations.management import getch

class Command(BaseCommand):
    help = "unfuck half baked swaps"
    def add_arguments(self, parser):
        parser.add_argument('room_one',
                           help='The First Room')
        parser.add_argument('room_two',
                           help='The Second Room')

    def handle(self, *args, **kwargs):
        if 'room_two' not in kwargs or \
           'room_one' not in kwargs:
            raise CommandError('must specify two rooms')

        one = kwargs['room_one']
        two = kwargs['room_two']
        room_one = None
        room_two = None
        try:
            room_one = Room.objects.get(number = one)
            room_two = Room.objects.get(number = two)
        except Room.DoesNotExist as exp:
            raise CommandError("must specify real rooms") from exp

        self.stdout.write(f"Room One number:{room_one.number} guest room number:{room_one.guest.room_number} primary:{room_one.primary} guest name: {room_one.guest.name}")
        self.stdout.write(f"Room Two number:{room_two.number} guest room number:{room_two.guest.room_number} primary:{room_two.primary} guest name: {room_two.guest.name}")

        if room_one.primary == room_one.guest.name or \
           room_two.primary == room_two.guest.name:
            raise CommandError("room/guest names match; not continuing")

        if room_one.number == room_one.guest.room_number or \
           room_two.number == room_two.guest.room_number:
            raise CommandError("room number / guest room number match; not continuing")

        self.stdout.write("Are You Suuuuuure [y/n]?")
        if getch().lower() != 'y':
            raise CommandError("user said nope")

        # fix guest number records
        room_one.guest.room_number = room_one.number
        room_two.guest.room_number = room_two.number

        # fix primary name
        room_two_primary = room_two.primary
        room_two.primary = room_one.primary
        room_one.primary = room_two_primary

        room_two.save()
        room_one.save()
        room_two.guest.save()
        room_one.guest.save()

        self.stdout.write(f"POST Room One number:{room_one.number} guest room number:{room_one.guest.room_number} primary:{room_one.primary} guest name: {room_one.guest.name}")
        self.stdout.write(f"POST Room Two number:{room_two.number} guest room number:{room_two.guest.room_number} primary:{room_two.primary} guest name: {room_two.guest.name}")
