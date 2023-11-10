from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from party.models import Party
from reservations.models import Room
from rest_framework import viewsets
from party.serializers import PartySerializer

class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    lookup_field = 'room_number'

    def create(self, request, *args, **kwargs):
        room_number = request.data['room_number']
        secret = request.data['secret']
        del request.data['secret']

        # we allow looking up the room by
        # * email
        # * primary name
        room = None
        try:
            room = Room.objects.get(name_hotel='Ballys', number=room_number)
            if secret.lower() not in [room.guest.email.lower(), room.primary.lower()]:
                return Response('is this really your room tho', status=status.HTTP_400_BAD_REQUEST)

        except Room.DoesNotExist:
            return Response('this room is not real', status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        existing = self.get_object()
        secret = request.data['secret']
        room = Room.objects.get(name_hotel = 'Ballys', number=existing.room_number)
        if secret not in [room.guest.email.lower(), room.primary.lower()]:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        existing.delete()
        return Response(status=status.HTTP_202_ACCEPTED)
