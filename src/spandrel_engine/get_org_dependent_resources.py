import json
import logging

import boto3
from botocore.exceptions import ClientError

from spandrel_engine.ae_logger import log_error
from spandrel_engine.constant import Constant
from spandrel_engine.lib.dynamodb import update_item, batch_write
from spandrel_engine.lib.sessions import get_session
from spandrel_engine.util import get_account_by_id, get_org_id

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))
report = []


def get_org_level_resources(region: str, account: dict, session, vmw_org_id, current_org_id, report) -> dict:
    status = Constant.StateMachineStates.COMPLETED

    analyzer_client = session.client('accessanalyzer', region_name=region)

    logger.debug(f"analyzer for region: {region}")

    analysers = analyzer_client.list_analyzers()['analyzers']

    if not analysers:
        msg = f"No Analyzer found in  region {region}"
        log_error(logger=logger, account_id=account['AccountId'], company_name=account['CompanyName'],
                  error_type=Constant.ErrorType.OLPE, msg=msg,
                  notify=True, slack_handle=account['SlackHandle'])
        update_item(Constant.DB_TABLE, account)
        return Constant.StateMachineStates.WAIT

    arn = analysers[0]['arn']

    # check for PrincipalOrgID
    org_level_resource_list = []

    for resource in analyzer_client.list_findings(analyzerArn=arn)['findings']:
        report.append(resource)

    if not vmw_org_id and not current_org_id:
        return status

    org_issues = [resource['resource'] for resource in analyzer_client.list_findings(
        analyzerArn=arn,
        filter={
            'condition.aws:PrincipalOrgID': {
                'contains': [
                    current_org_id]}
        })['findings'] if resource['status'] == 'ACTIVE']
    if org_issues:
        org_issues_resolved = [resource['resource'] for resource in analyzer_client.list_findings(
            analyzerArn=arn,
            filter={
                'condition.aws:PrincipalOrgID': {
                    'contains': [vmw_org_id]}
            })['findings'] if resource['status'] == 'ACTIVE']

        org_level_resource_list = list(set(org_issues).symmetric_difference(set(org_issues_resolved)))

    # check for PrincipalOrgID
    org_path_level_resource_list = []
    org_path_issue = [resource['resource'] for resource in analyzer_client.list_findings(
        analyzerArn=arn,
        filter=
        {
            'condition.aws:PrincipalOrgPaths': {
                'contains': [
                    current_org_id]}
        })['findings'] if resource['status'] == 'ACTIVE']
    if org_path_issue:
        org_path_resolved = [resource['resource'] for resource in analyzer_client.list_findings(
            analyzerArn=arn,
            filter={
                'condition.aws:PrincipalOrgPaths': {
                    'contains': [vmw_org_id]}
            })['findings'] if resource['status'] == 'ACTIVE']

        org_path_level_resource_list = list(set(org_path_issue).symmetric_difference(set(org_path_resolved)))

    org_level_permissions = org_level_resource_list + org_path_level_resource_list

    if org_level_permissions:
        status = Constant.StateMachineStates.WAIT
        for resource in org_level_permissions:
            msg = f"Resource {resource} is using organization level permission to access resource"
            log_error(logger=logger, account_id=account['AccountId'], company_name=account['CompanyName'],
                      error_type=Constant.ErrorType.OLPE, msg=msg,
                      notify=True, slack_handle=account['SlackHandle'])

        account["OrgLevelPermissions"] = org_level_permissions
        update_item(Constant.DB_TABLE, account)

    return status


def lambda_handler(event, context):
    logger.debug(f'Lambda event:{event}')
    status = set({})

    account_id = event["AccountId"]
    company_name = event['CompanyName']
    account = None

    try:
        account = get_account_by_id(company_name=company_name, account_id=account_id)[0]
        session = None
        if Constant.MASTER_ACCOUNT_ID != account_id:
            session = get_session(f"arn:aws:iam::{account_id}:role/{Constant.MASTER_ROLE}")
        if not session:
            session = boto3.session.Session()

        current_org_id = get_org_id(session=session)
        target_org_id = get_org_id()

        for region in event["Regions"]:
            get_org_level_resources(region, account, session, target_org_id, current_org_id, report)

        status = update_findings(report)

        if {Constant.StateMachineStates.WAIT}.issubset(status):
            event["Status"] = Constant.StateMachineStates.WAIT
        else:
            account["IsPermissionsScanned"] = True
            event["Status"] = Constant.StateMachineStates.COMPLETED

    except ClientError as ce:
        error_msg = log_error(logger=logger, account_id=event['AccountId'], company_name=event['CompanyName'],
                              error_type=Constant.ErrorType.OLPE, error=ce,
                              notify=True, slack_handle=account.get('SlackHandle'))
        account["Error"] = error_msg
        raise ce

    except Exception as ex:
        log_error(logger=logger, account_id=event['AccountId'], company_name=event['CompanyName'],
                  error_type=Constant.ErrorType.OLPE, notify=True, error=ex)
        raise ex
    finally:
        if account:
            update_item(Constant.DB_TABLE, account)

    return event


def update_findings(findings_data):
    # TODO : Tell system when to remove when to finish or wait
    # if {Constant.StateMachineStates.WAIT}.issubset(status):
    #     event["Status"] = Constant.StateMachineStates.WAIT
    # else:
    #     account["IsPermissionsScanned"] = True
    #     event["Status"] = Constant.StateMachineStates.COMPLETED

    findings = list({each['resource']: each for each in findings_data}.values())
    update_json = json.loads(json.dumps(findings, default=str))
    batch_write(Constant.FINDING_TABLE, update_json)

    # TODO Send report to configured email

    # TODO Check white listed accounts and organization from Account table and marked as resolved


if __name__ == '__main__':
    event = {
        "AccountId": "632616529567",
        "CompanyName": "iftikCompany",
        "Regions": [
            "eu-north-1",
            "ap-south-1",
            "eu-west-3",
            "eu-west-2",
            "eu-west-1",
            "ap-northeast-3",
            "ap-northeast-2",
            "ap-northeast-1",
            "sa-east-1",
            "ca-central-1",
            "ap-southeast-1",
            "ap-southeast-2",
            "eu-central-1",
            "us-east-1",
            "us-east-2",
            "us-west-1",
            "us-west-2"
        ]
    }
    lambda_handler(event, None)
