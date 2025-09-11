from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservations'
    verbose_name = 'Room Reservations'

    def ready(self):
        from reservations.checks import room_drama_check, guest_drama_check
