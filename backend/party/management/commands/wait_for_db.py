import time

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError

class Command(BaseCommand):
    """Wait for the database to be ready"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')

        while True:
            try:
                connection.cursor()
                break
            except OperationalError:
                pass
            self.stdout.write('Database unavailable, waiting 1 second...')
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database is ready'))
