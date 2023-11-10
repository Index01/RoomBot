import logging

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from waittime.models import Wait
from rest_framework import viewsets
import reservations.config as roombaht_config
from waittime.serializers import WaitViewSerializer, WaitListSerializer, WaitSerializer

class WaitViewSet(viewsets.ModelViewSet):
    queryset = Wait.objects.all()
    serializer_class = WaitSerializer
    lookup_field = 'short_name'

    def list(self, _request):
        serializer = WaitListSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, _request, *args, **kwargs):
        existing = self.get_object()
        serializer = WaitViewSerializer(existing)
        data = serializer.data
        if existing.password:
            data['has_password'] = True

        return Response(data)

    def destroy(self, request, *args, **kwargs):
        existing = self.get_object()
        if existing.password:
            if 'password' not in request.data:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            if existing.password != request.data['password']:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        existing.delete()
        return Response(status=status.HTTP_202_ACCEPTED)

    def update(self, request, *args, **kwargs):
        existing = self.get_object()
        actual_data = request.data

        if existing.password:
            if 'password' in actual_data and \
               existing.password == actual_data['password']:
                del actual_data['password']
            elif existing.free_update:
                if ('name' in request.data and request.data['name'] != existing.name) or \
                   ('countdown' in request.data and request.data['countdown'] != existing.countdown) or \
                       ('new_password' in request.data and request.data['new_password'] != existing.password) or \
                           ('free_update' in request.data and request.data['free_update'] != existing.free_update):
                    return Response('You can only modify time without knowing the password',
                                    status=status.HTTP_401_UNAUTHORIZED)

                actual_data = {
                    'time': request.data['time']
                }
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

        if 'new_password' in actual_data:
            actual_data['password'] = actual_data['new_password']

        serializer = WaitSerializer(existing, data=actual_data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)

        return Response(serializer.data)
