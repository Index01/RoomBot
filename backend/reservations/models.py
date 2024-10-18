import datetime
import logging
import sys
from django.utils.timezone import make_aware
from django.db import models
from django.contrib import admin
from reservations.constants import ROOM_LIST
from dirtyfields import DirtyFieldsMixin
from reservations.helpers import real_date
import reservations.config as roombaht_config

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)
logger = logging.getLogger('__name__')

class SwapError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(f"Unable to complete swap: {msg}")

class UnknownProductError(Exception):
    def __init__(self, product):
        self.product = product
        super().__init__(f"Unknown product: {product}")

class Guest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField("User Name", max_length=240)
    email = models.EmailField("Email")
    ticket = models.CharField("Ticket", max_length=20)
    transfer = models.CharField("Transfer", max_length=20)
    invitation = models.CharField("Invitation", max_length=20)
    jwt = models.CharField("Password", max_length=240)
    room_number = models.CharField("Room Number", max_length=20, blank=True, null=True)
    hotel = models.CharField("Hotel", max_length=20, null=True, blank=True)
    onboarding_sent = models.BooleanField("Onboarding Sent", default=False)
    can_login = models.BooleanField("Can Login", default=False)
    last_login = models.DateTimeField("Last Login", blank=True, null=True)

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

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    date_heiarchy = 'created_at'
    exclude = ['invitation', 'jwt', 'updated_at']
    fields = [
        ('name', 'email', 'onboarding_sent'),
        ('can_login', 'last_login'),
        ('ticket', 'transfer')
    ]
    readonly_fields = ['name', 'email', 'ticket', 'transfer', 'can_login',
                       'last_login']
    search_fields = ['name', 'email']
    description = 'A Guest'
    search_help_text = 'Search by username or email'

class Room(DirtyFieldsMixin, models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    number = models.CharField("Room Number", max_length=20)
    name_take3 = models.CharField("Room Type", max_length=50)
    name_hotel = models.CharField("Hotel", max_length=50)
    is_available = models.BooleanField("Available", default=False)
    is_swappable = models.BooleanField("Swappable", default=False)
    is_smoking = models.BooleanField("Smoking", default=False)
    is_lakeview = models.BooleanField("Lakeview", default=False)
    is_mountainview = models.BooleanField("Mountainview", default=False)
    is_ada = models.BooleanField("ADA", default=False)
    is_hearing_accessible = models.BooleanField("HearingAccessible", default=False)
    is_special = models.BooleanField("SpecialRoom", default=False)
    is_placed = models.BooleanField("PlacedRoom", default=False)
    swap_code = models.CharField("SwapCode", max_length=200, blank=True, null=True)
    swap_time = models.DateTimeField(blank=True, null=True)
    _check_in = models.DateField(blank=True, null=True, db_column='check_in')
    _check_out = models.DateField(blank=True, null=True, db_column='check_out')
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
        elif value and value != '':
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

        elif value and value != '':
            self._check_in = real_date(value)

        elif value == '':
            self._check_in = None

    def swappable(self):
        return self.guest \
            and self.is_swappable \
            and (not self.is_special)

    def cooldown(self):
        if not self.swap_time:
            return False

        chill_time = self.swap_time \
            + datetime.timedelta(seconds=roombaht_config.ROOM_COOLDOWN)
        right_now = make_aware(datetime.datetime.utcnow())
        return chill_time.timestamp() > right_now.timestamp()

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
        if product.lower().startswith('nugget'):
            return 'Nugget'

        if product.lower().startswith('bally'):
            return 'Ballys'

        raise UnknownProductError(product)

    @staticmethod
    def swap(room_one, room_two):
        if room_two.name_take3 != room_two.name_take3:
            logger.warning("Attempt to swap mismatched room types %s (%s) - %s (%s)",
                           room_one.number, room_two.name_take3,
                           room_two.number, room_two.name_take3)
            raise SwapError('mismatched room type')

        if not room_one.swappable():
            logger.warning("Attempted to swap non swappable room %s %s",
                           room_one.name_hotel, room_one.number)
            raise SwapError('Room one is not swappable')

        if not room_two.swappable():
            logger.warning("Attempted to swap non swappable room %s %s",
                           room_two.name_hotel, room_two.number)
            raise SwapError('Room two is not swappable')

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

        room_one_sp_ticket_id = room_one.sp_ticket_id
        room_one.sp_ticket_id = room_two.sp_ticket_id
        room_two.sp_ticket_id = room_one_sp_ticket_id

        # we force this for both rooms to enable swap cooldown time
        room_one.swap_time = make_aware(datetime.datetime.utcnow())
        room_two.swap_time = make_aware(datetime.datetime.utcnow())

        room_two.save()
        room_one.save()

        room_two.guest.save()
        room_one.guest.save()


@admin.register(Room)
class RoomsAdmin(admin.ModelAdmin):
    exclude = ['created_at',
               'updated_at',
               'swap_code']
    fields = [
        ('number', 'name_take3', 'name_hotel'),
        ('is_placed', 'primary', 'secondary', 'check_in', 'check_out'),
        ('is_smoking', 'is_lakeview', 'is_special',
         'is_hearing_accessible', 'is_mountainview', 'placed_by_roombot',
         'sp_ticket_id')
    ]
    readonly_fields = [
        'check_in', 'check_out', 'is_smoking', 'is_lakeview', 'is_special',
        'is_hearing_accessible', 'is_mountainview', 'is_placed',
        'placed_by_roombot', 'sp_ticket_id'
    ]
    description = 'A Room'
    list_display = [
        'number',
        'name_hotel',
        'name_take3'
    ]
    search_fields = [
        'number',
        'name_hotel',
        'name_take3',
        'primary',
        'secondary'
    ]
    search_help_text = 'Search by room number, hotel name' \
        'room type, and primary or secondary name'

    sortable_by = [
        'number',
        'name_hotel',
        'name_take3'
    ]
