import logging
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError
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


def list_bucket_objects(client, bucket_name: str) -> List:
    """List the objects in an Amazon S3 bucket

    :param bucket_name: string
    :return: List of bucket objects. If error, return None.
    """

    # Retrieve the list of bucket objects
    try:
        response = client.list_objects_v2(Bucket=bucket_name)
    except ClientError as err:
        # AllAccessDisabled error == bucket not found
        logging.error(err)
        return None

    # Only return the contents if we found some keys
    if response['KeyCount'] > 0:
        return response['Contents']

    return None
