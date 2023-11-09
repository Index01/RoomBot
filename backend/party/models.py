from django.db import models
from reservations.models import Room

class Party(models.Model):
    room_number = models.CharField("RoomNumber", max_length=10, unique=True)
    description = models.CharField("Description", max_length=50)

    def __str__(self):
        return (self.room_number, self.description)
