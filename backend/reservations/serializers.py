



from rest_framework import serializers
from .models import Guest, Room, Party

class RoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = ('number', 'name_take3', 'name_hotel', 'available', 'guest')


class GuestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Guest
        fields = ('name', 'email', 'ticket', 'invitation', 'room_number')


class PartySerializer(serializers.ModelSerializer):

    class Meta:
        model = Party
        fields = ('room_number', 'description', 'end_time')

