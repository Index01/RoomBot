from getpass import getpass
from django.core.management.base import BaseCommand, CommandError
from reservations.models import Guest, Staff
from reservations.auth import reset_otp

class Command(BaseCommand):
    help = "Make modifications to a user"
    def add_arguments(self, parser):
        parser.add_argument('email',
                            help='The email to search for')

        parser.add_argument('-p', '--password',
                            help='Regenerate password (otp/jwt) and send reset email',
                            action='store_true',
                            default=False)

        parser.add_argument('--resend-onboarding',
                            help='Mark the user to have their onboarding email sent again',
                            action='store_true',
                            default=False)

    def handle(self, *args, **kwargs):
        if 'email' not in kwargs:
            raise CommandError("Must specify email")

        if 'adult' in kwargs and \
           kwargs['adult'].lower() not in ['admin', 'staff', 'none']:
            raise CommandError('Invalid option passed to --adult')

        guest_entries = Guest.objects.filter(email=kwargs['email'])
        if guest_entries.count() == 0:
            raise CommandError(f"No user found with email {kwargs['email']}")

        if kwargs['password']:
            self.stdout.write("Resetting user password...")
            reset_otp(kwargs['email'])

        if kwargs['resend_onboarding']:
            self.stdout.write("Unsetting activation sent...")
            for guest in guest_entries:
                guest.onboarding_sent = False
                guest.save()
