from django.db import models
from reservations.constants import ROOM_LIST
from dirtyfields import DirtyFieldsMixin
from reservations.helpers import real_date
import datetime

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
    hotel = models.CharField("Hotel", max_length=20, null=True, blank=True)
    onboarding_sent = models.BooleanField("OnboardingSent", default=False)
    can_login = models.BooleanField("CanLogin", default=False)
    last_login = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    @staticmethod
    def traverse_transfer(chain):
        obj = chain[-1]
        if not obj.transfer:
            return chain

        guest = Guest.objects.get(ticket=obj.transfer)
        chain.append(guest)
        if guest.transfer:
            return Guest.traverse_transfer(chain)

        return chain

    def chain(self):
        return Guest.traverse_transfer([self])


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
    is_mountainview = models.BooleanField("MountainviewRoom", default=False)
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
        if isinstance(value, datetime.date):
            self._check_out = value
        elif value != '':
            self._check_out = real_date(value)
        elif value == '':
            self._check_out = None

    @property
    def check_in(self):
        return self._check_in

    @check_in.setter
    def check_in(self, value):
        if isinstance(value, datetime.date):
            self._check_in = value

        elif value != '':
            self._check_in = real_date(value)

        elif value == '':
            self._check_in = None

    def swappable(self):
        return self.guest \
            and self.is_swappable \
            and (not self.is_special)

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

    @staticmethod
    def short_product_code(product):
        for a_room, a_product in ROOM_LIST.items():
            if product in a_product:
                return a_room

        if product in ROOM_LIST.keys():
            return product

        raise Exception('Should never not find a short product code tho')

    @staticmethod
    def derive_hotel(product):
        if product.lower().startswith('hard rock'):
            return 'Hard Rock'

        if product.lower().startswith('bally'):
            return 'Ballys'

        if product.lower().startswith('art room bally'):
            return 'Ballys'

        raise Exception(f"Unable to resolve hotel for {product}")

    @staticmethod
    def swap(room_one, room_two):
        room_two.guest.room_number = room_one.number
        room_one.guest.room_number = room_two.number

        room_one.swap_code = None
        guest_id_theirs = room_one.guest
        room_one.guest = room_two.guest
        room_two.guest = guest_id_theirs

        room_one_primary = room_one.primary
        room_one_secondary = room_one.secondary
        room_one.primary = room_two.primary
        room_two.primary = room_one_primary

        if room_two.secondary:
            room_one.secondary = room_two.secondary

        if room_one.secondary:
            room_two.secondary = room_one_secondary

        room_one_check_in = room_one.check_in
        room_one_check_out = room_one.check_out
        room_one.check_in = room_two.check_in
        room_one.check_out = room_two.check_out
        room_two.check_in = room_one_check_in
        room_two.check_out = room_one_check_out

        room_one_guest_notes = room_one.guest_notes
        room_one.guest_notes = room_two.guest_notes
        room_two.guest_notes = room_one_guest_notes

        room_one_sp_ticket_id = room_one.sp_ticket_id
        room_one.sp_ticket_id = room_two.sp_ticket_id
        room_two.sp_ticket_id = room_one_sp_ticket_id

        room_two.save()
        room_one.save()

        room_two.guest.save()
        room_one.guest.save()
