
import os
import logging
import jwt
import datetime
import json
import sys
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from ..models import Guest
from ..models import Room
from ..models import Staff
from ..helpers import phrasing, send_email
import reservations.config as roombaht_config

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger('ViewLogger_login')

def update_last_login(guest):
    for a_guest in Guest.objects.filter(email=guest.email):
        a_guest.last_login = datetime.datetime.now()
        a_guest.save()

@api_view(['POST'])
def login(request):
    if request.method == 'POST':
        data = request.data

        logger.info(f"[+] User login attempt: {data['email']}")
        try:
            email = data['email']
        except KeyError:
            logger.info(f"[-] User login failed {data['email']}")
            return Response("User not found", status=status.HTTP_400_BAD_REQUEST)
        guests = Guest.objects.all()
        guest_email = guests.filter(email=email)
        staff = Staff.objects.all()
        staff_email = staff.filter(email=email)
        jwt_key = roombaht_config.JWT_KEY
        # Check if login attempt is admin
        for admin in staff_email:
            if data['jwt'] == admin.guest.jwt:
                resp = jwt.encode({"email":admin.email,
                                   "datetime":str(datetime.datetime.utcnow())},
                                   jwt_key,
                                  algorithm="HS256")
                logger.info(f"[+] Admin login succes. sending resp")
                update_last_login(admin.guest)
                return Response(str(json.dumps({"jwt": resp})), status=status.HTTP_201_CREATED)

        # Check if login attempt is guest
        for guest in guest_email:
            if data['jwt'] == guest.jwt:
                resp = jwt.encode({"email":guest.email,
                                   "datetime":str(datetime.datetime.utcnow())},
                                   jwt_key, algorithm="HS256")
                logger.info(f"[+] User login succes. sending resp")
                update_last_login(guest)
                return Response(str(json.dumps({"jwt": resp})), status=status.HTTP_201_CREATED)
        return Response("Invalid credentials", status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_reset(request):
    if request.method == 'POST':
        try:
            data = request.data["guest"]
            email = data["email"]
        except KeyError as e:
            logger.info(f"[+] Reset fail missing field: {data['email']}")
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)
        logger.info(f"[+] User reset attempt: {data['email']}")

        new_pass = phrasing()
        try:
            guests = Guest.objects.all()
            guest_email = guests.filter(email=email)[0]
            guest_email.jwt=new_pass
            guest_email.save()
        except (IndexError, KeyError) as e:
            logger.info(f"[-] User reset failed {data['email']}")
            return Response("User not found", status=status.HTTP_400_BAD_REQUEST)

        body_text = f"Hi I understand you requested a RoomService Roombaht password reset?\nHere is your shiny new password: {new_pass}\n\nIf you did not request this reset there must be something strang happening in the neghborhood. Please report any suspicious activity.\nGood luck."

        send_email([guest_email.email],
                   'RoomService RoomBaht - Password Reset',
                   body_text
                   )

        return Response(status=status.HTTP_201_CREATED)
