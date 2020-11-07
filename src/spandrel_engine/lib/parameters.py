import logging

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_secured_parameter(param_name, is_secured):
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(
        Name=param_name, WithDecryption=is_secured
    )
    return response['Parameter'].get('Value')
