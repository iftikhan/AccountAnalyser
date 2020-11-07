"""Code used to get sessions in the various AWS accounts needed as part of account assimilation"""
import logging

import boto3.session

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_session(role_arn, session=boto3.session.Session(), session_name='VmwAccountAssimilationEngine'):
    """Assumes a role and returns a boto3.session.Session() for that role.

    if session is provided will use that session for the basis of assuming the role.
    This is useful when "hopping" through master accounts to linked accounts.

    """
    sts = session.client('sts')
    get_caller_identity = sts.get_caller_identity()
    logger.info(f"Getting session for {role_arn} as {get_caller_identity['Arn']}")

    sts = session.client('sts')
    assume_role_response = sts.assume_role(
        DurationSeconds=900,
        RoleArn=role_arn,
        RoleSessionName=session_name
    )

    role_keys = assume_role_response['Credentials']
    session = boto3.session.Session(
        aws_access_key_id=role_keys['AccessKeyId'],
        aws_secret_access_key=role_keys['SecretAccessKey'],
        aws_session_token=role_keys['SessionToken']
    )
    logger.debug(f"Got boto3 Session with AccessKeyId {role_keys['AccessKeyId']}")

    return session
