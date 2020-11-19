import json
import logging
from time import sleep

import boto3
from botocore.exceptions import ClientError

from spandrel_engine.constant import Constant
from spandrel_engine.lib.sessions import get_session

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))


def get_org_id(session=None):
    try:
        org_client = session.client('organizations') if session else boto3.client('organizations')
        return org_client.describe_organization()['Organization']['Id']
    except Exception as ex:
        return None


def get_parent_id(session=None, account_id=None, parent_type=None):
    org_client = session.client('organizations') if session else boto3.client('organizations')
    parents = org_client.list_parents(
        ChildId=account_id
    )['Parents']
    for parent in parents:
        if parent['Type'] == parent_type:
            return parent['Id']


def create_roles(session):
    account_id = session.client('sts').get_caller_identity()['Account']
    logging.info(f'Creating roles for AccountId {account_id}')

    iam_client = session.client('iam')

    roles_to_create = sorted(Constant.ROLE_CONFIG.keys())
    created_roles = []
    for role in roles_to_create:
        try:
            iam_client.get_role(RoleName=role)
            logger.info(f'Role {role} already exist in AccountId {account_id}')
        except ClientError as ce:
            if ce.response['Error']['Code'] == 'NoSuchEntity':
                logger.info(f"Creating role {role} in AccountId {account_id}")
                import os
                iam_client.create_role(
                    RoleName=role,
                    AssumeRolePolicyDocument=json.dumps(Constant.ROLE_CONFIG[role]['TrustPolicy'])
                )
                role_policy = Constant.ROLE_CONFIG[role]['Policy']
                if type(role_policy) is dict:
                    iam_client.put_role_policy(
                        RoleName=role,
                        PolicyName='RolePolicy',
                        PolicyDocument=json.dumps(role_policy)
                    )
                else:
                    iam_client.attach_role_policy(
                        PolicyArn=role_policy,
                        RoleName=role
                    )
                created_roles.append(role)
                iam_client.get_waiter('role_exists').wait(RoleName=role)
                # Notes: Check MasterRole as we are going to use this role very moment after
                # creation. As role policy takes time to reflect, assume role fails. We will be assuming role to
                # make sure role and attached policies are in effect.
                if role == Constant.MASTER_ROLE:
                    while True:
                        try:
                            get_session(f"arn:aws:iam::{account_id}:role/{role}")
                            break
                        except ClientError as ce:
                            # Note: Don't raise any Exception/Error as we are expecting client error if role is not
                            # in effect. Once role is in effect.
                            sleep(2)
                            pass
            else:
                raise ce

    return created_roles
