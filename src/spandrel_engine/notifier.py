import json
import logging
from datetime import datetime

from spandrel_engine.constant import Constant
from spandrel_engine.lib.notification import notify_msg

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))

"""
Message structure
message = {
        "Title": "Assimilation Engine",
        "AccountId": "account_id",
        "CompanyName": "company_name",
        "Type": "error_type",
        "Message": "formatted_error_msg",
        "Error": "error",
        "ErrorCode": "error_code",
        "ErrorMessage": "error_message"
    }
"""


def lambda_handler(event, context):
    logger.info(event)
    msg = event
    if not msg.get('SlackMessage'):
        account_id = msg["AccountId"]

        title = f" {msg['Type']} \n Company: {msg['CompanyName']}"
        color = '#4caf50'

        if account_id and account_id != '':
            title = title + f"- AccountId: {account_id}"

        if event.get('Type'):
            color = '#d84315'

        if event.get('ActionItem'):
            title = f"User Action required for {title}"
            color = '#ffc107'

        text = f'```{json.dumps(event)}```' if not event.get('ActionItem') else event.get('ActionItem')

        message = dict({
            'SlackMessage': {
                'attachments': [
                    {
                        'color': color,
                        'author_name': title,
                        'author_icon': Constant.AUTHOR_ICON,
                        'title': Constant.NOTIFICATION_TITLE,
                        'text': text,
                        'footer': Constant.NOTIFICATION_NOTES,
                        'ts': datetime.now().timestamp()
                    }]
            }
        })
    else:
        message = msg
    if msg.get('SlackHandle'):
        message["WebhookUrl"] = msg.get('SlackHandle')
    notify_msg(Constant.SLACK_TOPIC, Constant.NOTIFICATION_TITLE, json.dumps(message))
