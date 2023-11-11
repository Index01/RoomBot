from rest_framework import serializers
from party.models import Party

class PartySerializer(serializers.ModelSerializer):

    class Meta:
        model = Party
        fields = ('room_number', 'description')
