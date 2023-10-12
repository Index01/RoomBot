
import os
import logging
import jwt
import datetime
import json
import environ
import sys
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from ..models import Guest
from ..models import Room
from ..models import Staff
from .rooms import phrasing


logging.basicConfig(stream=sys.stdout,
                    level=os.environ.get('ROOMBAHT_LOGLEVEL', 'INFO').upper())

logger = logging.getLogger('ViewLogger_login')

SEND_MAIL = os.environ.get('ROOMBAHT_SEND_MAIL', False)

@api_view(['POST'])
def login(request):
    if request.method == 'POST':
        env = environ.Env()
        environ.Env.read_env()
        try:
            key = env("ROOMBAHT_JWT_KEY")
        except ImproperlyConfigured as e:
            logger.error("jwt env key missing")
            return Response("Invalid credentials", status=status.HTTP_400_BAD_REQUEST)

        data = request.data["guest"]
        logger.debug(f'data: {data}')

        logger.info(f"[+] User login attempt: {data['email']}")
        try:
            email = data['email']
        except KeyError as e:
            logger.info(f"[-] User login failed {data['email']}")
            return Response("User not found", status=status.HTTP_400_BAD_REQUEST)
        guests = Guest.objects.all()
        guest_email = guests.filter(email=email)
        staff = Staff.objects.all()
        staff_email = staff.filter(email=email)

        # Check if login attempt is admin
        for admin in staff_email:
            if data['jwt'] == admin.guest.jwt:
                resp = jwt.encode({"email":admin.email,
                                   "datetime":str(datetime.datetime.utcnow())},
                                   key, algorithm="HS256")
                logger.debug(f'returning: {resp}')
                logger.info(f"[+] Admin login succes. sending resp")
                return Response(str(json.dumps({"jwt": resp})), status=status.HTTP_201_CREATED)

        # Check if login attempt is guest
        for guest in guest_email:
            logger.debug(f"[+] in: {data['jwt']} db {guest.jwt}")
            if data['jwt'] == guest.jwt:
                resp = jwt.encode({"email":guest.email,
                                   "datetime":str(datetime.datetime.utcnow())},
                                   key, algorithm="HS256")
                logger.debug(f'returning: {resp}')
                logger.info(f"[+] User login succes. sending resp")
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
        logger.debug(f'reset: {data}')
        logger.info(f"[+] User reset attempt: {data['email']}")

        new_pass = phrasing()
        logger.debug(f'phrase: {new_pass}')
        try:
            guests = Guest.objects.all()
            guest_email = guests.filter(email=email)[0]
            guest_email.jwt=new_pass
            guest_email.save()
        except (IndexError, KeyError) as e:
            logger.info(f"[-] User reset failed {data['email']}")
            return Response("User not found", status=status.HTTP_400_BAD_REQUEST)

        logger.debug(f'sending email to {guest_email.email}')
        body_text = f"Hi I understand you requested a RoomService Roombaht password reset?\nHere is your shiny new password: {new_pass}\n\nIf you did not request this reset there must be something strang happening in the neghborhood. Please report any suspicious activity.\nGood luck."
        if(SEND_MAIL==True):
            send_mail("RS Roombaht Password Reset",
                      body_text,
                      "placement@take3presents.com",
                      [guest_email.email],
                      auth_user=os.environ['ROOMBAHT_EMAIL_HOST_USER'],
                      auth_password=os.environ['ROOMBAHT_EMAIL_HOST_PASSWORD'],
                      fail_silently=False,)


        logger.info(f"[+] User pass reset and sent: {data['email']}")
        return Response(status=status.HTTP_201_CREATED)
