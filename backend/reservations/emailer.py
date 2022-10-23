
import environ
import mailchimp_transactional as MailchimpTransactional
from mailchimp_transactional.api_client import ApiClientError


env = environ.Env()
environ.Env.read_env()
key = env("MAILCHIMP_API")
mailchimp = MailchimpTransactional.Client(key)



def connection_test():
    print(f'key:{mailchimp.api_key}')
    try:
        response = mailchimp.users.ping()
        print(f"[+] Email ping success: {response}")
    except ApiClientError as e:
        print(f"[-] Email ping failre: {e.status_code}")



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
        print(f"[+] Email sent to {recipient}")
    except ApiClientError as e:
        print(f"[-] Email send fail {e.text}")

