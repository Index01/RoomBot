from rest_framework import serializers
from .models import Guest, Room

class RoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = ('number', 'name_take3', 'name_hotel', 'is_available', 'guest', 'is_swappable')


class GuestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Guest
        fields = ('name', 'email', 'ticket', 'invitation', 'room_number')
