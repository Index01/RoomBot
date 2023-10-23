from django.core.management.base import BaseCommand, CommandError
from reservations.models import Guest

class Command(BaseCommand):
    help = "Show information on a guest/user"
    def add_arguments(self, parser):
        parser.add_argument('email',
                            help='The email to search for')

    def handle(self, *args, **kwargs):
        if 'email' not in kwargs:
            raise CommandError("Must specify email")

        guest_entries = Guest.objects.filter(email=kwargs['email'])
        if len(guest_entries) == 0:
            raise CommandError(f"No user found with email {kwargs['email']}")

        guest = guest_entries[0]
        self.stdout.write(f"User {guest.name}, otp: {guest.jwt}")
