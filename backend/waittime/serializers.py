from rest_framework import serializers
from waittime.models import Wait

class WaitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wait
        fields = ['created_at', 'updated_at', 'name', 'short_name', 'time', 'password']

class WaitViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wait
        fields = ['created_at', 'updated_at', 'name', 'short_name', 'time']

class WaitListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wait
        fields = ['name', 'short_name']

