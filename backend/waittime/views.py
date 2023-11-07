import logging

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from waittime.models import Wait
from rest_framework import viewsets
import reservations.config as roombaht_config
from waittime.serializers import WaitSerializer, WaitListSerializer

class WaitViewSet(viewsets.ModelViewSet):
    queryset = Wait.objects.all()
    serializer_class = WaitSerializer
    lookup_field = 'short_name'

    def list(self, request):
        serializer = WaitListSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)
