from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from reservations.helpers import send_email, phrasing, my_url, ingest_csv


class Command(BaseCommand):
    def create_staff(self, init_file):
        _staff_fields, staff = ingest_csv(init_file)

        for staff_new in staff:
            existing_staff = None
            try:
                existing_staff = User.objects.get(email = staff_new['email'])
            except User.DoesNotExist:
                pass

            if existing_staff:
                self.stdout.write(f"Staff {existing_staff.email} already exists")
                continue

            otp = phrasing()
            staff = User(username=staff_new['name'],
                         email=staff_new['email'],
                         password=otp)
            staff.save()

            self.stdout.write(f"Created staff: {staff_new['name']}, admin: {staff_new['is_admin']}")

            hostname = my_url()

            body_text = f"""
                Congratulations, u have been deemed Staff worthy material.

                Email {staff_new['email']}
                Admin {otp}

                login at {hostname}/login
                then go to {hostname}/admin
                Good Luck, Starfighter.

            """
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
