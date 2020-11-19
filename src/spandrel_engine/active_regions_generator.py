import logging

import boto3

from spandrel_engine.constant import Constant
from spandrel_engine.lib.sessions import get_session

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))


def get_enabled_regions(account_id=None):
    session = None
    if Constant.MASTER_ACCOUNT_ID != account_id:
        session = get_session(f"arn:aws:iam::{account_id}:role/{Constant.MASTER_ROLE}")
    if not session:
        session = boto3.session.Session()

    ec2 = session.client('ec2')
    describe_regions = ec2.describe_regions(
        Filters=[
            {'Name': 'opt-in-status',
             'Values': ['opt-in-not-required']}  # Regions that support v1 sts tokens
        ]
    )
    region_names = [region['RegionName'] for region in describe_regions['Regions']]

    return region_names


def lambda_handler(event, context):
    logger.debug(event)

    if type(event) is list:
        event = event[0]
    event = event['Data']
    account_id = boto3.client('sts').get_caller_identity().get('Account')

    event["Regions"] = get_enabled_regions(account_id=account_id)
    return event
