
import os
import logging
import jwt
import datetime
import json
import environ
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import Staff
from ..models import Guest
from ..models import Room
from .rooms import phrasing


logging.basicConfig(filename='../output/roombaht_application.md',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
logging.info("Admin Views Logger")

logger = logging.getLogger('ViewLogger_admin')

SEND_MAIL = os.environ['SEND_MAIL']

env = environ.Env()

@api_view(['POST'])
def staff(request):
    if request.method == 'POST':
        try:
            data = request.data["staff"]
            staff_all = Staff.objects.all()
            staff_email = staff_all.filter(email=data['email'])
        except KeyError as e:
            logger.info(f"[-] Missing fields {data.data}")
            return Response("User not found", status=status.HTTP_400_BAD_REQUEST)


        for staff in staff_email:
            print(f"[+] in: {data['jwt']} db {staff.jwt}")
            if data['jwt'] == staff.guest.jwt and staff.is_admin==True:

                print("staff is admin")
                resp = "success"
                return Response(str(json.dumps({"resp": resp})), status=status.HTTP_200_OK)

        return Response("Invalid credentials", status=status.HTTP_400_BAD_REQUEST)
