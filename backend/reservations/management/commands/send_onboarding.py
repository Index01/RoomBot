import logging
from random import randint
import sys
import time
from django.core.management.base import BaseCommand, CommandError
import reservations.config as roombaht_config
from reservations.models import Guest
from reservations.helpers import my_url, send_email

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)
logger = logging.getLogger('SendOnboarding')

def onboarding_email(email, otp):
    hostname = my_url()
    body_text = f"""
        BleepBloopBleep!

        This is the Room Service RoomBaht. I'm an automated tool for swapping rooms in Bally's. The floors have been cleaned and you have been assigned a room! No bucket or mop needed.

        After you login below, you can view where your room is placed, look at each floor's layout, and send swap requests to other rooms.  You can only swap rooms until Sunday, November 5, at 5pm PST, so please make sure you are happy with the room you have or swap swiftly.

        Here's how to swap rooms with someone:
        1. Find a room you want to swap with (it must be the same room type).
        2. Click "SendSwapRequest" and enter in how you'd like the other room's owner to contact you—probably your email address or phone number. You can send swap requests to many rooms, but you can only swap with one of them.
        3. The owner of the room you want will contact you. Or not. If you already know who they are, you can reach out directly.
        4. If you both agree to swap rooms, login (link below) and find the room you want to swap under "My Rooms."
        5. Click CreateSwapCode. Give this swap code to the other person.
        6. The other person has 10 minutes to log into Roombaht, click "EnterSwapCode" for the room that they are swapping with you, and enter the swap code.
        7. Magic intradimensional elves will hop around and inform you of your success. And you will have the new room of your dreams!

        This is your password. There are many like it, but this one is yours. Once you use this password on a device, RoomBaht will remember you, but only on that device.

        Copy and paste this password. Because let's face it, no one should trust humans to make passwords:
        username: {email}
        password: {otp}
        login page: {hostname}/login

        Good Luck, Starfighter.

        It should go without saying, but don't forward this email.


    """
    send_email([email],
               'RoomService RoomBaht - Account Activation',
               body_text)

class Command(BaseCommand):
    help = "Send batches of onboarding emails for guests"
    def add_arguments(self, parser):
        parser.add_argument('-b', '--batch-size',
                            help=f"Batch size to use, defaults to {roombaht_config.ONBOARDING_BATCH}",
                            default=roombaht_config.ONBOARDING_BATCH)

    def handle(self, *args, **kwargs):
        emails = Guest.objects \
            .filter(onboarding_sent=False, room_number__isnull=False) \
            .order_by('?') \
            .values('email') \
            .distinct()[:int(kwargs['batch_size'])]

        emails_length = emails.count()
        logger.debug("Found %s guests who have not had a onboarding email sent", emails_length)

        if emails_length == 0:
            self.stdout.write("No more activation emails left")

        for email in [x['email'] for x in emails]:
            guests = Guest.objects.filter(email = email)
            onboarded = [x for x in guests if x.onboarding_sent]
            if len(onboarded) == 0:
                logger.debug("Activation email for %s has never been sent", email)
                if not roombaht_config.SEND_ONBOARDING:
                    logger.debug("Not actually sending onboarding email to %s", email)
                else:
                    onboarding_email(email, guests[0].jwt)

            not_onboarded = [x for x in guests if not x.onboarding_sent]
            if len(not_onboarded) > 0:
                logger.debug("Updating onboarding_sent for %s guest records for %s",
                             len(not_onboarded), email)
                for guest in not_onboarded:
                    guest.onboarding_sent = True
                    guest.save()

            time.sleep(randint(2, 5))
