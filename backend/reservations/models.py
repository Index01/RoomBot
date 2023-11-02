from django.db import models
from dirtyfields import DirtyFieldsMixin
from reservations.helpers import real_date

class Guest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField("Name", max_length=240)
    email = models.EmailField()
    ticket = models.CharField("Ticket", max_length=20)
    transfer = models.CharField("Transfer", max_length=20)
    invitation = models.CharField("Invitation", max_length=20)
    jwt = models.CharField("JWT", max_length=240)
    room_number = models.CharField("RoomNumber", max_length=20, blank=True, null=True)
    onboarding_sent = models.BooleanField("OnboardingSent", default=False)
    last_login = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

class Staff(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField("Name", max_length=240)
    email = models.EmailField()
    is_admin = models.BooleanField("Admin", default=False)
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f'staff name: {self.name}'

class Room(DirtyFieldsMixin, models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    number = models.CharField("Number", max_length=20)
    name_take3 = models.CharField("Take3Name", max_length=50)
    name_hotel = models.CharField("HotelName", max_length=50)
    is_available = models.BooleanField("Available", default=False)
    is_swappable = models.BooleanField("IsSwappable", default=False)
    is_smoking = models.BooleanField("SmokingRoom", default=False)
    is_lakeview = models.BooleanField("LakeviewRoom", default=False)
    is_ada = models.BooleanField("ADA", default=False)
    is_hearing_accessible = models.BooleanField("HearingAccessible", default=False)
    is_art = models.BooleanField("ArtRoom", default=False)
    is_special = models.BooleanField("SpecialRoom", default=False)
    is_comp = models.BooleanField("CompRoom", default=False)
    is_placed = models.BooleanField("PlacedRoom", default=False)
    swap_code = models.CharField("SwapCode", max_length=200, blank=True, null=True)
    swap_time = models.DateTimeField(blank=True, null=True)
    _check_in = models.DateField(blank=True, null=True, db_column='check_in')
    _check_out = models.DateField(blank=True, null=True, db_column='check_out')
    notes = models.TextField(blank=True, verbose_name='RoomNotes')
    guest_notes = models.TextField(blank=True, verbose_name='GuestNotes')
    sp_ticket_id = models.CharField("SecretPartyTicketID", max_length=20, blank=True, null=True)
    primary = models.CharField("PrimaryContact", max_length=50)
    secondary = models.CharField("SecondaryContact", max_length=50)
    placed_by_roombot = models.BooleanField("PlacedByRoombot", default=False)
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return str(self.number)

    @property
    def check_out(self):
        return self._check_out

    @check_out.setter
    def check_out(self, value):
        if value != '':
            self._check_out = real_date(value)
        elif value == '':
            self._check_out = None

    @property
    def check_in(self):
        return self._check_in

    @check_in.setter
    def check_in(self, value):
        if value != '':
            self._check_in = real_date(value)

        elif value == '':
            self._check_in = None

    def swappable(self):
        return self.guest \
            and self.is_swappable \
            and (not self.is_art) \
            and (not self.is_special) \
            and (not self.is_comp)

    def hotel_sku(self):
        sku = None
        if self.name_take3 == 'Queen':
            sku = 'Standard 2 Queens'
        elif self.name_take3 == 'Queen Sierra Suite':
            sku = 'Sierra 2 Queens Suite'
        elif self.name_take3 == 'King':
            sku = 'Standard King'
        elif self.name_take3 == 'Queen':
            sku = 'Standard Queen'
        elif self.name_take3 == 'King Sierra Suite':
            sku = 'Sierra King Suite'
        elif self.name_take3 == 'Tahoe Suite':
            sku = 'Tahoe King Suite'
        elif self.name_take3 == 'Executive Suite':
            sku = 'Executive King Suite'
        else:
            sku = self.name_take3

        if self.is_lakeview:
            sku = f"Lakeview {sku}"

        if self.is_smoking:
            sku = f"{sku} (Smoking)"

        access = []
        if self.is_hearing_accessible:
            access.append('Hearing Accessible')

        if self.is_ada:
            access.append('ADA')

        if len(access) > 0:
            sku = (f"{sku} ({','.join(access)})")

        return sku
