import logging
from datetime import datetime

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def batch_write(table, items, is_account_data=False):
    with get_db(table).batch_writer() as batch:
        for item in items:
            # if target account data then add extra column
            if is_account_data:
                item["AccountStatus"] = 0
                item["AccountId"] = item["AccountId"].zfill(12)
                item["IsPermissionsScanned"] = False
                item["LastUpdatedOn"] = datetime.utcnow().isoformat()
            batch.put_item(Item=convert_empty_values(item))


def update_item(table, item):
    item["LastUpdatedOn"] = datetime.utcnow().isoformat()
    get_db(table).put_item(Item=convert_empty_values(item))


def get_db(table):
    db_client = boto3.resource('dynamodb')
    return db_client.Table(table)


# Note: Python AWS sdk doesn't support "convertEmptyValues"
# iftik: This util function should take care of empty string in inset record.
# Added fix for nested list
def convert_empty_values(d):
    for k in d:
        if isinstance(d[k], dict):
            convert_empty_values(d[k])
        elif isinstance(d[k], list):
            for i in d[k]:
                if isinstance(i, list) or isinstance(i, dict):
                    convert_empty_values(i)
        elif d[k] == "":
            d[k] = None
    return d
