from django.core.management.base import BaseCommand, CommandError
from jinja2 import Environment, PackageLoader
from reservations.models import Guest, Staff
from reservations.helpers import send_email, phrasing, my_url, ingest_csv


class Command(BaseCommand):
    def create_staff(self, init_file):
        _staff_fields, staff = ingest_csv(init_file)

        for staff_new in staff:
            existing_staff = None
            try:
                existing_staff = Staff.objects.get(email = staff_new['email'])
            except Staff.DoesNotExist:
                pass

            if existing_staff:
                self.stdout.write(f"Staff {existing_staff.email} already exists")
                continue

            otp = phrasing()
            guest=Guest(name=staff_new['name'],
                        email=staff_new['email'],
                        jwt=otp)
            guest.save()

            staff=Staff(name=staff_new['name'],
                        email=staff_new['email'],
                        guest=guest,
                        is_admin=staff_new['is_admin'])
            staff.save()

            self.stdout.write(f"Created staff: {staff_new['name']}, admin: {staff_new['is_admin']}")

            objz = {
                'hostname': my_url(),
                'password': otp,
                'email': staff_new['email']
            }
            jenv = Environment(loader=PackageLoader('reservations'))
            template = jenv.get_template('staff.j2')
            body_text = template.render(objz)
            send_email([staff_new['email']],
                       'RoomService RoomBaht - Staff Activation',
                       body_text)

    help = "Batch creates roombot adults based on CSV"
    def add_arguments(self, parser):
        parser.add_argument('staff_file',
                            help='Path to staff CSV')


    def handle(self, *args, **kwargs):
        if 'staff_file' not in kwargs:
            raise CommandError('Must specify a staff csv file')

        self.create_staff(kwargs['staff_file'])
