import json
import logging
import time

import boto3

from spandrel_engine.constant import Constant

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))

"""
Message structure
message = {
        'Title': 'Assimilation Engine',
        'AccountId': account_id,
        'CompanyName': company_name,
        'Type': error_type,
        'Message': formatted_error_msg,
        'Error': error,
        'ErrorCode': error_code,
        'ErrorMessage': error_message
    }
"""


def lambda_handler(event, context):
    logger.debug(f'Lambda event:{event}')
    msg = event['Records'][0]['Sns']['Message']
    return handle_error(json.loads(msg))


def handle_error(error: dict):
    sfn_client = boto3.client('stepfunctions')
    sfn_client.start_execution(stateMachineArn=Constant.NOTIFICATION_OBSERVER_ARN,
                               name=f"{error.get('CompanyName') or 'General'}-"
                                    f"{error.get('AccountId') or 'Notification'}-"
                                    f"{error.get('ErrorCode') or ''}-{time.monotonic_ns()}", input=json.dumps(error))
