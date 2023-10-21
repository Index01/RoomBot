import datetime
import logging
import jwt
import sys
from rest_framework import status
from rest_framework.response import Response
import reservations.config as roombaht_config
from reservations.models import Guest, Staff

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)
logger = logging.getLogger('ViewLogger_auth')

def authenticate(request):
    data = request.data
    try:
        jwt_data=data["jwt"]
    except KeyError as e:
        logger.warning("[-] JWT information missing ip:%s data: %s, e: %s", request.META['REMOTE_ADDR'], data, e)
        return None

    try:
        dec = jwt.decode(jwt_data, roombaht_config.JWT_KEY, algorithms="HS256")
    except (TypeError, jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
        logger.warning("[-] Unable to decode jwt ip:%s", request.META['REMOTE_ADDR'])
        return None

    dthen = datetime.datetime.fromisoformat(dec["datetime"])
    dnow = datetime.datetime.utcnow()

    email = dec['email']
    if dnow - dthen > datetime.timedelta(days=1):
        logger.info("[-] JWT has expired email:%s ip:%s", request.META['REMOTE_ADDR'], email)
        return None

    try:
        _guest = Guest.objects.filter(email=dec['email'])
    except Guest.DoesNotExist:
        logger.warning("[-] No guest found. email:%s ip:%s", email, request.META['REMOTE_ADDR'])

    return {'email': email, 'admin': False}

def authenticate_admin(request):
    auth_obj = authenticate(request)
    if not auth_obj or 'email' not in auth_obj:
        return None

    staff = None
    try:
        staff = Staff.objects.get(email=auth_obj['email'])
    except Staff.DoesNotExist:
        logger.warning("[-] No staff found. email:%s ip:%s", auth_obj['email'], request.META['REMOTE_ADDR'])
        return None

    if staff.is_admin:
        auth_obj['admin'] = True

    return auth_obj

def unauthenticated():
    return Response("[-] Unauthorized", status=status.HTTP_401_UNAUTHORIZED)
