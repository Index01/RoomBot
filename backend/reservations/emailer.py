"""MailChimp
2023.10.12 STILL BEING DEVELOPED
"""

import sys
import os

import logging
import mailchimp_transactional as MailchimpTransactional
from mailchimp_transactional.api_client import ApiClientError


logging.basicConfig(stream=sys.stdout,
                    level=os.environlogging.INFO)
logger = logging.getLogger('EmailerLogger')

mailchimp = MailchimpTransactional.Client(os.environ['MAILCHIMP_API'])



def connection_test():
    try:
        response = mailchimp.users.ping()
        logger.debug(f"[+] Email ping success: {response}")
    except ApiClientError as e:
        logger.error(f"[-] Email ping failre: {e.status_code}")



def send_mail(subject, body, recipient, bcc=None):
    message = {
               "from_email": "RoomBaht@roomservice.com",
               "from_name": "RoomBaht9000",
               "subject": f"{subject}",
               "text": f"{body}",
               "to": [{
                   "email": "{recipient}",
                   "type": "to"
               }]
              }
    try:
        response = mailchimp.messages.send({"message":message})
        logger.info(f"[+] Email sent to {recipient}")
    except ApiClientError as e:
        logger.error(f"[-] Email send fail {e.text}")
