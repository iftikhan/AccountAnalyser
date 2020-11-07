import logging

from spandrel_engine.ae_logger import log_error
from spandrel_engine.constant import Constant
from spandrel_engine.util import get_account_by_id

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))


def lambda_handler(event, context):
    logger.debug(f'Lambda event:{event}')
    event["Status"] = get_account_scan_status(event)
    return event


def get_account_scan_status(event: dict) -> str:
    event = event.get("Data") or event
    try:
        account = get_account_by_id(company_name=event['CompanyName'], account_id=event['AccountId'])[0]
    except Exception as ex:
        log_error(logger=logger, account_id=event["AccountId"], company_name=event['CompanyName'],
                  error_type=Constant.ErrorType.OLPE, notify=True, error=ex)
        raise ex

    return Constant.StateMachineStates.COMPLETED if account.get("IsPermissionsScanned") \
        else Constant.StateMachineStates.WAIT
