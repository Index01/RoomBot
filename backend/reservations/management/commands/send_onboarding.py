import logging
import sys
from django.core.management.base import BaseCommand, CommandError
import reservations.config as roombaht_config
from reservations.models import Guest
from reservations.helpers import my_url, send_email

logging.basicConfig(stream=sys.stdout, level=roombaht_config.LOGLEVEL)
logger = logging.getLogger('SendOnboarding')

def onboarding_email(email, otp):
    hostname = my_url()
    body_text = f"""
        BleepBloopBleep, this is the Room Service RoomBaht for Room Swaps letting you know the floors have been cleaned and you have been assigned a room. No bucket or mop needed.

        After you login below you can view your current room, look at other rooms and send trade requests. This functionality is only available until Sunday 11/5 at 5pm PST, so please make sure you are good with what you have or trade early.

        Here's how to swap rooms with someone:
        1. Find your desired room with the same room type (eg queen).
        2. Click "SendSwapRequest" and enter in information about how you'd like the owner to contact you, eg email address or phone #.
        3. They will contact you. Or not. Or if you already know who has the room you want, reach out directly.
        4. If you both agree to swap rooms, login (link below) and find the room you want to swap under "My Rooms".
        5. Click CreateSwapCode. Give this swap code to the other person.
        6. Within 10 minutes, they need to go to their page, click "EnterSwapCode" for the room you want, and enter the swap code.
        7. Magic intradimensional elves will hop around and inform you of your success. And you will have the room you always wanted!

        Really, if you have a friend that you want to swap rooms with, just get their swap code for their room and enter it for your released room.

        Goes without saying, but don't forward this email.

        This is your password, there are many like it but this one is yours. Once you use this password on a device, RoomBaht will remember you, but only on that device.
        Copy and paste this password. Because let’s face it, no one should trust humans to make passwords:
        {otp}
        {hostname}/login

        Good Luck, Starfighter.

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
            .filter(onboarding_sent=False) \
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
