from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from reservations.models import Guest
from jinja2 import Environment, PackageLoader
from reservations.helpers import send_email, phrasing, my_url, ingest_csv


def staff_onboarding(email, otp):
    objz = {
        'hostname': my_url(),
        'password': otp,
        'email': email
    }
    jenv = Environment(loader=PackageLoader('reservations'))
    template = jenv.get_template('staff.j2')
    body_text = template.render(objz)
    send_email([email],
               'RoomService RoomBaht - Staff Activation',
               body_text)

class Command(BaseCommand):
    def create_staff(self, args):
        staff_file = args['staff_file']
        _staff_fields, staff = ingest_csv(staff_file)

        for staff_new in staff:
            existing_staff = None
            try:
                existing_staff = User.objects.get(email = staff_new['email'])
            except User.DoesNotExist:
                pass

            if existing_staff:
                self.stdout.write(f"Staff {existing_staff.email} already exists")
                if args['always_send']:
                    staff_onboarding(existing_staff.guest.email, existing_staff.guest.jwt)

                continue

            otp = phrasing()
            guest=Guest(name=staff_new['name'],
                        email=staff_new['email'],
                        jwt=otp)
            guest.save()

            staff = User(username=staff_new['name'],
                         email=staff_new['email'],
                         is_staff=True,
                         is_superuser=staff_new['is_admin'])
            staff.set_password(otp)
            staff.save()

            self.stdout.write(f"Created staff: {staff_new['name']}, admin: {staff_new['is_admin']}")
            staff_onboarding(guest.email, otp)

    help = "Batch creates roombot adults based on CSV"
    def add_arguments(self, parser):
        parser.add_argument('staff_file',
                            help='Path to staff CSV')
        parser.add_argument('--always-send',
                            help='Always send staff onboarding email, even if already in system',
                            action='store_true',
                            default=False)

    def handle(self, *args, **kwargs):
        if 'staff_file' not in kwargs:
            raise CommandError('Must specify a staff csv file')

        self.create_staff(kwargs)
