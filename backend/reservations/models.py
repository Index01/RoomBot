from django.db import models

class Guest(models.Model):
    name = models.CharField("Name", max_length=240)
    email = models.EmailField()
    ticket = models.CharField("Ticket", max_length=20)
    invitation = models.CharField("Invitation", max_length=20)
    jwt = models.CharField("JWT", max_length=240)
    notes = models.TextField(blank=True, verbose_name='GuestNotes')
    room_number = models.CharField("RoomNumber", max_length=20)

    def __str__(self):
        return self.name

class Staff(models.Model):
    name = models.CharField("Name", max_length=240)
    email = models.EmailField()
    is_admin = models.BooleanField("Admin", default=False)
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f'staff name: {self.name}'

class Room(models.Model):
    number = models.CharField("Number", max_length=20)
    name_take3 = models.CharField("Take3Name", max_length=50)
    name_hotel = models.CharField("HotelName", max_length=50)
    is_available = models.BooleanField("Available", default=False)
    is_swappable = models.BooleanField("IsSwappable", default=False)
    is_smoking = models.BooleanField("SmokingRoom", default=False)
    is_lakeview = models.BooleanField("LakeviewRoom", default=False)
    is_ada = models.BooleanField("ADA", default=False)
    is_hearing_accessible = models.BooleanField("HearingAccessible", default=False)
    swap_code = models.CharField("SwapCode", max_length=200, blank=True, null=True)
    swap_time = models.DateTimeField(blank=True, null=True)
    check_in = models.DateField(blank=True, null=True)
    check_out = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, verbose_name='RoomNotes')
    guest_notes = models.TextField(blank=True, verbose_name='GuestNotes')
    sp_ticket_id = models.CharField("SecretPartyTicketID", max_length=20)
    secondary = models.CharField("SecondaryContact", max_length=50)
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return str(self.number)
