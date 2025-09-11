from getpass import getpass
from django.core.management.base import BaseCommand, CommandError
from reservations.models import Guest
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

        parser.add_argument('--login',
                            help='Enable user logins',
                            default=False,
                            action='store_true')

        parser.add_argument('--no-login',
                            help='Disable user logins',
                            default=False,
                            action='store_true')


    def handle(self, *args, **kwargs):
        if 'email' not in kwargs:
            raise CommandError("Must specify email")

        guest_entries = Guest.objects.filter(email=kwargs['email'])
        if guest_entries.count() == 0:
            raise CommandError(f"No user found with email {kwargs['email']}")

        if kwargs['password']:
            self.stdout.write("Resetting user password...")
            reset_otp(kwargs['email'])

        guest_count = 0
        for guest in guest_entries:
            # remove this once guest record uses dirtyfieldmixin
            guest_changed = False
            if kwargs['resend_onboarding']:
                self.stdout.write("Unsetting activation sent...")
                guest.onboarding_sent = False
                guest_changed = True


            if kwargs['login'] and not guest.can_login:
                guest.can_login = True
                guest_changed = True
            elif kwargs['no_login'] and guest.can_login:
                guest.can_login = False
                guest_changed = True

            if guest_changed:
                guest.save()
                guest_count += 1


        if guest_count > 0:
            self.stdout.write(f"Updated {guest_count} guest records")
