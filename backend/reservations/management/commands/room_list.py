from django.core.management.base import BaseCommand, CommandError
from reservations.models import Room

class Command(BaseCommand):
    help = "List all rooms"

    def handle(self, *args, **kwargs):
        for room in Room.objects.all():
            placed_msg = 'yes' if room.is_placed else 'no'
            comp_msg = 'yes' if room.is_comp else 'no'
            art_msg = 'yes' if room.is_comp else 'no'
            special_msg = 'yes' if room.is_special else 'no'
            avail_msg = 'yes' if not room.is_available else 'no'
            msg = (
                f"{room.name_hotel:10}{room.number:5}{room.hotel_sku():40} "
                f"Available: {avail_msg:4}"
                f"Placed:{placed_msg:4} Comp:{comp_msg:4} Art:{art_msg:4} Special:{special_msg:4}"
            )
            self.stdout.write(msg)

