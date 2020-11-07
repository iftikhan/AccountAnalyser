import logging

import boto3

from spandrel_engine.constant import Constant
from spandrel_engine.lib.sessions import get_session

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))


def lambda_handler(event, context):
    logger.debug(f'Lambda event:{event}')
    return create_analyzer(event)


def create_analyzer(event: dict) -> dict:
    regions = event["Regions"]
    account_id = event["AccountId"]
    session = None
    if Constant.MASTER_ACCOUNT_ID != account_id:
        session = get_session(f"arn:aws:iam::{account_id}:role/{Constant.MASTER_ROLE}")
    if not session:
        session = boto3.session.Session()

    for region in regions:
        analyzer_client = session.client('accessanalyzer', region_name=region)

        if len(analyzer_client.list_analyzers()['analyzers']) == 0:
            analyzer = analyzer_client.create_analyzer(

                analyzerName=f"default_analyzer_{region}",
                type='ACCOUNT'
            )
            logger.debug(f"Analyzer {analyzer} created for region {region}")
        else:
            logger.debug(f"Analyzer already exist for region {region}")
    return event
