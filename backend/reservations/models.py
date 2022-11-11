from django.db import models


class Guest(models.Model):
    name = models.CharField("Name", max_length=240)
    email = models.EmailField()
    ticket = models.CharField("Ticket", max_length=20)
    invitation = models.CharField("Invitation", max_length=20)
    jwt = models.CharField("JWT", max_length=240)
    room_number = models.CharField("RoomNumber", max_length=20)

    def __str__(self):
        return self.name

class Room(models.Model):
    number = models.CharField("Number", max_length=20)
    name_take3 = models.CharField("Take3Name", max_length=20)
    name_hotel = models.CharField("HotelName", max_length=20)
    available = models.BooleanField("Available", default=True)
    swap_code = models.CharField("SwapCode", max_length=200, blank=True, null=True)
    swap_time = models.DateTimeField(blank=True, null=True)
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return str(self.number)

class Party(models.Model):
    room_number = models.CharField("RoomNumber", max_length=20)
    description = models.CharField("Description", max_length=50, blank=True, null=True)
    end_time = models.DateTimeField("EndTime", blank=True, null=True)

    def __str__(self):
        return (self.room_number, self.description, self.end_time)



