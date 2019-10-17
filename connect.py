import logging
from typing import Dict, Any
import boto3

from config import get_config


def connect_mturk() -> boto3.session.Session:
    aws: Dict[str, Any] = get_config('aws')
    mturk: Dict[str, Any] = get_config('mturk')

    client = boto3.client('mturk',
                         aws_access_key_id=aws['access_key_id'],
                         aws_secret_access_key=aws['secret_access_key'],
                         region_name=aws['region_name'],
                         endpoint_url=mturk['endpoint_url'])

    logging.info("Successfully connected to the MTurk account")

    balance = client.get_account_balance()['AvailableBalance']
    logging.debug(f"I have ${balance} in my account")

    return client
