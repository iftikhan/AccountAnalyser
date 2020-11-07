import logging

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def notify_msg(topic, subject, message):
    sns = boto3.resource('sns')
    topic = sns.Topic(topic)
    if type(message).__name__.__ne__('str'):
        message = str(message)
    topic.publish(
        Message=message,
        Subject=subject,
        MessageStructure='string'
    )
