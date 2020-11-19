import logging
import os

from botocore.exceptions import ClientError

from spandrel_engine.lib.parameters import get_secured_parameter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_lambda_param(pram, is_ssm: bool = False, is_ssm_secured: bool = False):
    message = None
    data = os.environ.get(pram)

    if not data:
        message = f"Environment param {pram} not found"
    if is_ssm and data:
        try:
            data = get_secured_parameter(data, is_ssm_secured)
        except ClientError as ce:
            message = repr(ce)
    if message:
        logger.warning(message)
    return data


class Constant:
    # Lambda Parameters

    # DB_TABLE = get_lambda_param('TARGET_ACCOUNT_TABLE_NAME')
    # FINDING_TABLE = get_lambda_param('FINDINGS_TABLE')
    LOG_LEVEL = get_lambda_param('LOG_LEVEL') or 'INFO'
    EMAIL_ADDRESSES = get_lambda_param('EMAIL_ADDRESSES').split(',') if get_lambda_param(
        'EMAIL_ADDRESSES') else None

    WHITE_LISTED_ORGS = get_lambda_param('WHITE_LISTED_ORGS').split(',') if get_lambda_param(
        'WHITE_LISTED_ORGS') else None

    WHITE_LISTED_ACCOUNTS = get_lambda_param('WHITE_LISTED_ACCOUNTS').split(',') if get_lambda_param(
        'WHITE_LISTED_ACCOUNTS') else None

    # Lambda Status
    FAILED = 0
    SUCCESS = 1

    # STRING BOOL
    FALSE = 'FALSE'
    TRUE = 'TRUE'

    # Slack
    AUTHOR_NAME = 'Spandrel Engine'
    AUTHOR_ICON = 'https://i.ibb.co/R3Bs1BS/AE.png'

    # Error Type
    class ErrorType:
        AIE = "Account Integrity Error"
        CATE = 'Check Account Type Error'
        CE = "Constant Error"
        CHE = 'Cloud health Error'
        COUE = "Change OU Error"
        CRLE = 'Create master role in Linked account  Error'
        CRME = 'Create master role in Master account error'
        CUE = 'Cleanup Error'
        NHE = "Notification Handler Error"
        JOE = 'Join Organization Error'
        LDE = 'Load Data Error'
        LOE = 'Leave Organization Error'
        OLPE = "Org Level Resource Permission Scan Error"
        RGE = "Report Generation Error"

    # SNS Email
    NOTIFICATION_NOTES = "\n\n\n Note: For more info please check DynamoDB AssimilationEngineTable's Error column, " \
                         "Step function and CloudWatch lambda logs"
    NOTIFICATION_TITLE = 'Assimilation Engine'

    DEFAULT_OU_ID = get_lambda_param('VMW_DEFAULT_OU_ID')

    MASTER_ROLE = 'VMWMasterRole'

    class StateMachineStates:
        COMPLETED = 'Completed'
        CONCURRENCY_WAIT = 'ConcurrencyWait'
        LINKED_ACCOUNT_FLOW = 'LinkedAccountFlow'
        STANDALONE_ACCOUNT_FLOW = 'StandaloneAccountFlow'
        WAIT = 'Wait'

    # Org parent typo
    class OrgParentType:
        ROOT = 'ROOT'
        OU = 'ORGANIZATIONAL_UNIT'

    class AccountStatus:
        INVITED = 1  # Account has left the current organization and ready to accept invitation.
        JOINED = 2  # Account has joined new organization.
        UPDATED = 3  # Account is moved to default OU.
        MONITORED = 4  # Account is registered with Cloudhealth.
        LEFT = 5  # Account has left the current organization and left to be closed/suspended.
        SUSPENDED = 6  # Account is closed/suspended.

    # AccountType Codes
    class AccountType:
        LINKED = 'Linked'
        MASTER = 'Master'
        STANDALONE = 'Standalone'

    @staticmethod
    def get_support_case_desc(account_id):
        return f"This company has been acquired by VMWare. " \
               f"This payer account i.e.{account_id} and all linked accounts will be migrated into the VMware AWS " \
               f"Organization. " \
               f"To facilitate this migration, we need the payment method updated for this payer " \
               f"account({account_id}) and all linked accounts. " \
               f"The phone number verification may be needed for each account too" \
               f"This is necessary to allow linked accounts to leave this AWS Organization and join the " \
               f"VMware AWS Organization. " \
               f"If invoice info is presently on any of the accounts we understand you cannot update the " \
               f"info so please leave as it is." \
               f"\r\n \r\nPlease update this payer account({account_id}) and all linked accounts " \
               f"with the below details:\r\n \r\n" \
               f"PO Number: 221553\r\n" \
               f"Company Name: VMware Inc\r\n" \
               f"Billing Contact Name: Accounts Payable\r\n" \
               f"Billing address / Default payment method address: 3401 HILLVIEW AVE, PALO ALTO, CA 94304-1320 US\r\n" \
               f"Billing contact phone: 1-877-486-9273\r\n" \
               f"Contact email for invoice: aws-inv-notices@vmware.com\r\n \r\n" \
               f"Net Term (to match new payer): 45 days\r\n \r\n" \
               f"Please close this case once the payment method for the payer account({account_id}) and " \
               f"all linked accounts have been updated. " \
               f"This support request has been opened via automation. " \
               f"This automation will check the status of the request periodically to see if this request " \
               f"has been closed and will then proceed with it's next tasks.\r\n \r\n" \
               f"Humans are CCed on this request, so if you need further information please reply to the case " \
               f"and a human will respond to your inquiry."
