import boto3
from botocore.exceptions import ClientError

from spandrel_engine.constant import Constant


def send_email(html_report):
    SENDER = f"Spandrel Engine <{Constant.EMAIL_ADDRESSES}>"
    RECIPIENT = Constant.EMAIL_ADDRESSES
    AWS_REGION = "us-east-1"
    SUBJECT = "Spandrel Engine Report"

    BODY_HTML = html_report

    CHARSET = "UTF-8"

    client = boto3.client('ses', region_name=AWS_REGION)

    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    }
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,

        )
    except ClientError as e:
        (e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
