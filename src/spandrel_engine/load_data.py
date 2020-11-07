import json
import logging
from datetime import datetime

from spandrel_engine.ae_logger import log_error
from spandrel_engine.constant import Constant
from spandrel_engine.lib.data import get_account_data
from spandrel_engine.lib.dynamodb import batch_write
from spandrel_engine.lib.notification import notify_msg
from spandrel_engine.util import get_accounts_by_company_name

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))


def generate_account_updates(company_name: str, account_data: list):
    existing_accounts = get_accounts_by_company_name(company_name=company_name)
    existing_account_id_list = [record['AccountId'] for record in existing_accounts]
    new_accounts = [account for account in account_data
                    if not account['AccountId'].zfill(12) in existing_account_id_list]
    for account in new_accounts:
        # Since all accounts in the file must be from the same company only the first record must have the company name.
        if account.get('CompanyName') and account['CompanyName'] != company_name:
            raise ValueError(
                "All accounts must belong to the same company."
            )

    return new_accounts


def lambda_handler(event, context):
    logger.debug(f'Lambda event:{event}')
    company_name = event['CompanyName']
    s3_url = f"s3://{Constant.SHARED_RESOURCE_BUCKET}/{event['FilePath']}"

    try:
        account_data = get_account_data(s3_url)
        account_updates = generate_account_updates(company_name, account_data)
        if account_updates:
            account_ids = [account['AccountId'] for account in account_updates]
            logger.info(f"Loading account data for company {company_name} for the following AccountIds: {account_ids}")
            batch_write(Constant.DB_TABLE, account_updates, is_account_data=True)
        else:
            logging.warning(f"No new account for company {company_name} included in {s3_url}")

        notify_data = {
            'SlackHandle': None,
            'SlackMessage': {
                'attachments': [
                    {
                        'color': '#0ec1eb',
                        'author_name': Constant.AUTHOR_NAME,
                        'author_icon': Constant.AUTHOR_ICON,
                        'title': 'Assimilation Engine Started',
                        'text': f"Assimilation Engine Started for company {company_name}",
                        'footer': Constant.NOTIFICATION_NOTES,
                        'ts': datetime.now().timestamp()
                    }]
            }}
        notify_msg(Constant.NOTIFICATION_TOPIC, Constant.NOTIFICATION_TITLE, json.dumps(notify_data))

    except Exception as ex:
        log_error(logger=logger, account_id=None, company_name=company_name,
                  error_type=Constant.ErrorType.LDE, notify=True, error=ex)
        raise ex

    return {"Status": Constant.StateMachineStates.COMPLETED, "CompanyName": company_name}
