from django.core.mail import EmailMessage, get_connection



def send_aws_email():
    ses_client = boto3.client("ses", region_name="us-west-2")
    CHARSET = "UTF-8"
    
    response = ses_client.send_email(
    Destination={
        "ToAddresses": [
        "",
        ],
    },
    Message={
        "Body": {
            "Text": {
                "Charset": CHARSET,
                "Data": "BleepBloop",
            }
        },
    "Subject": {
        "Charset": CHARSET,
        "Data": "RoomBot test",
        },
    },
    Source="",
    )


bod = "Log Dump"
conn = get_connection()
msg = EmailMessage(subject="RoomBaht Logging - log dump", 
                   body=bod, 
                   to=["jeff@take3presents.com", "tyler32bit@gmail.com"],
                   connection=conn)
msg.attach_file('../output/log_script_out.md')

msg.send()

