import json
import logging

import boto3
from botocore.exceptions import ClientError

from spandrel_engine.constant import Constant
from spandrel_engine.lib.dynamodb import update_item
from spandrel_engine.lib.sessions import get_session
from spandrel_engine.reports import generate_report
from spandrel_engine.util import get_org_id

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))
report = []


def get_account_level_resources(region: str, account: dict, session, report) -> dict:
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

    for resource in analyzer_client.list_findings(analyzerArn=arn)['findings']:
        report.append(resource)

    return status


def lambda_handler(event, context):
    logger.debug(f'Lambda event:{event}')
    status = set({})

    account_id = event["AccountId"]
    # company_name = event['CompanyName']
    account = event

    try:
        # account = get_account_by_id(company_name=company_name, account_id=account_id)[0]
        session = None
        if Constant.MASTER_ACCOUNT_ID != account_id:
            session = get_session(f"arn:aws:iam::{account_id}:role/{Constant.MASTER_ROLE}")
        if not session:
            session = boto3.session.Session()

        current_org_id = get_org_id(session=session)
        target_org_id = get_org_id()

        for region in event["Regions"]:
            get_account_level_resources()(region, account, session, report)

        status = update_findings(report, account)

        if status:
            event["Status"] = Constant.StateMachineStates.WAIT
        else:
            event["Status"] = Constant.StateMachineStates.COMPLETED

    except ClientError as ce:
        raise ce

    except Exception as ex:
        raise ex
    finally:
        if account:
            update_item(Constant.DB_TABLE, account)

    return event


def update_findings(findings_data, account):
    unique_findings = list({each['resource']: each for each in findings_data}.values())
    findings = json.loads(json.dumps(unique_findings, default=str))

    white_listed_accounts = account.get("WhiteListAccounts")
    white_listed_orgs = account.get("WhiteListOrgs")
    for finding in findings:
        if finding.get("principal") and finding.get("principal").get("AWS"):
            principals = finding["principal"]["AWS"]
            if type(principals).__name__ == "list":
                for principal in principals:
                    for account in white_listed_accounts:
                        if account in principal:
                            finding["WhiteListed"] = True
                        else:
                            finding["WhiteListed"] = False

            elif principals in white_listed_accounts:
                finding["WhiteListed"] = True
            else:
                finding["WhiteListed"] = False

        if finding.get("condition") and finding.get("principal").get("AWS"):
            if finding["principal"]["AWS"] in white_listed_orgs:
                finding["WhiteListed"]

    # batch_write(Constant.FINDING_TABLE, findings)

    generate_report(findings)
    return False


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
