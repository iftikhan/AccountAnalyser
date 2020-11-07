import logging
import time

from spandrel_engine.constant import Constant
from spandrel_engine.lib.dynamodb import get_db

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))
"""
Fetch all record belongs to target company names.
"""


def get_accounts(company_name):
    # Custom query
    accounts = get_db(Constant.DB_TABLE).query(
        ProjectionExpression="CompanyName, AccountId",
        KeyConditionExpression='CompanyName = :cn',
        FilterExpression=' AccountStatus < :as',
        ExpressionAttributeValues=
        {':cn': company_name,
         ':as': Constant.AccountStatus.MONITORED}).get('Items')

    for acc in accounts:
        acc["ProcessName"] = f"{acc['CompanyName']}-{acc['AccountId']}-{time.monotonic_ns()}"

    return accounts


def lambda_handler(event, context):
    logger.debug(f'Lambda event:{event}')
    company_name = event['CompanyName']
    return {'CompanyName': company_name, 'Accounts': get_accounts(company_name)}
