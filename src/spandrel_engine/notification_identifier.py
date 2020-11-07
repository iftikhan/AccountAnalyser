import logging

from spandrel_engine.constant import Constant

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, Constant.LOG_LEVEL))


def lambda_handler(event, context):
    logger.debug(f'Lambda event:{event}')
    event["handler"] = identify_error(event)
    return event


def identify_error(error_msg: dict) -> object:
    error_code = error_msg.get("ErrorCode")

    # Error Handler mapping
    error_handlers = {
        "ConstraintViolationException": 'constraint_violation_exception_handler(error)',
        "HandshakeConstraintViolationException": "handshake_constraint_violation_exception_handler(error)",
        "DuplicateAccountException": "duplicate_account_exception_handler(error)"
    }
    return error_handlers.get(error_code, "Notify")
