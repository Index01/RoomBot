from django.core.management.base import BaseCommand, CommandError
from reservations.models import Guest, Staff

class Command(BaseCommand):
    help = "Show information on a guest/user"
    def add_arguments(self, parser):
        parser.add_argument('email',
                            help='The email to search for')

    def handle(self, *args, **kwargs):
        if 'email' not in kwargs:
            raise CommandError("Must specify email")

        guest_entries = Guest.objects.filter(email=kwargs['email'])
        if guest_entries.count() == 0:
            raise CommandError(f"No user found with email {kwargs['email']}")

        guest = guest_entries[0]
        last_login = 'never'
        if guest.last_login:
            ll = guest.last_login
            last_login = f"{ll.month}/{ll.day}/{ll.year} {ll.hour}:{ll.minute}"

        onboarding = 'no'
        if guest.onboarding_sent:
            onboarding = 'yes'

        rooms = ','.join([f"{x.hotel} {x.room_number}" for x in guest_entries if x.room_number])
        if len(rooms) == 0:
            rooms = 'none'

        tickets = ','.join([x.ticket for x in guest_entries if x.ticket])
        if len(tickets) == 0:
            tickets = 'none'

        adult = ''
        try:
            staff = Staff.objects.get(email=guest.email)
            adult = ' [staff'
            if staff.is_admin:
                adult += ' & admin'

            adult += '],'
        except Staff.DoesNotExist:
            pass

        self.stdout.write(f"User {guest.name},{adult} otp: {guest.jwt}, last login: {last_login}")
        self.stdout.write(f"    rooms: {rooms}, tickets: {tickets}, onboarding sent: {onboarding}")
