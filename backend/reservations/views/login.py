
import os
import logging
import jwt
import datetime
import json
import sys
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from constance import config
from django.core.mail import send_mail
from django.utils.timezone import make_aware
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from ..models import Guest
from ..models import Room
from ..helpers import phrasing, send_email
import reservations.config as roombaht_config
from reservations.auth import reset_otp

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)

logger = logging.getLogger('ViewLogger_login')

def update_last_login(guest):
    for a_guest in Guest.objects.filter(email=guest.email):
        a_guest.last_login = make_aware(datetime.datetime.utcnow())
        a_guest.save()

@api_view(['POST', 'GET'])
def login(request):
    if request.method == 'GET':
        data = {
            'features': roombaht_config.features()
        }
        return Response(data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        data = request.data

        if 'email' not in data or \
           'jwt' not in data:
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)

        email = data['email']
        guest_email = Guest.objects.filter(email=email, can_login=True)
        try:
            admin_email = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response("invalid credentials", status=status.HTTP_401_UNAUTHORIZED)

        jwt_key = roombaht_config.JWT_KEY
        admin_user = authenticate(username=admin_email.username,
                                  password=data['jwt'])
        if admin_user is not None:
            resp = jwt.encode({"email":admin_user.email,
                               "datetime":str(datetime.datetime.utcnow())},
                              jwt_key,
                              algorithm="HS256")
            logger.info("[+] Admin login success for %s", admin_user.email)
            body = {"jwt": resp, "admin": True}
            return Response(body, status=status.HTTP_201_CREATED)

        # Check if login attempt is guest
        for guest in guest_email:
            if data['jwt'] == guest.jwt:
                resp = jwt.encode({"email":guest.email,
                                   "datetime":str(datetime.datetime.utcnow())},
                                   jwt_key, algorithm="HS256")
                logger.info("[+] User login success for %s", guest.email)
                update_last_login(guest)
                return Response({"jwt": resp}, status=status.HTTP_201_CREATED)

        logger.debug("No valid credentials found for %s", email)
        return Response("Invalid credentials", status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def login_reset(request):
    if request.method == 'POST':
        try:
            data = request.data["guest"]
            email = data["email"].lower()
        except KeyError as e:
            logger.info(f"[+] Reset fail missing field: email")
            return Response("missing fields", status=status.HTTP_400_BAD_REQUEST)

        logger.info("[+] User reset attempt: %s", email)
        reset_otp(email)

        return Response(status=status.HTTP_201_CREATED)
