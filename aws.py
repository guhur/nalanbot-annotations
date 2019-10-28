import logging
import yaml
from typing import Dict, Any, List
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from tqdm.auto import tqdm
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


def list_all_hits(client: boto3.session.Session):
    """
    Return all HITs connected to current account
    """
    hits = []
    response = client.list_hits()

    while 'NextToken' in response and response['NextToken'] != "":
        response = client.list_hits(NextToken=response['NextToken'])
        hits += response['HITs']

    return hits


def list_recorded_hits(client: boto3.session.Session):
    """
    Return all HITs stored in job.yaml
    """
    config = get_config()

    with open(config['job_filename'], "r") as fid:
        hits = yaml.safe_load(fid)

    return hits



def delete_hit(client: boto3.session.Session, hit_id: str):
    try:
        # If HIT is active then set it to expire immediately
        status = client.get_hit(HITId=hit_id)['HIT']['HITStatus']
        if status == 'Assignable':
            response = client.update_expiration_for_hit(
                HITId=hit_id,
                ExpireAt=datetime(2015, 1, 1)
            )
        client.delete_hit(HITId=hit_id)

    except:
        logging.error(f"Can't delete {hit_id}")


def delete_recorded_hits(client: boto3.session.Session):
    """
    Delete all HITs present in job.yaml
    """
    records = list_recorded_hits(client)

    for record in tqdm(records):
        delete_hit(client, record['HITId'])

def delete_all_hits(client: boto3.session.Session):

    records = list_all_hits(client)

    for record in tqdm(records):
        delete_hit(client, record['HITId'])


def get_hit_progress(client: boto3.session.Session, hit_id: str
                    ) -> List[int]:
    """
    Return the number of completed assignements wrt.
    total number of assignements
    """
    hit = client.get_hit(HITId=hit_id)['HIT']
    total = int(hit['MaxAssignments'])
    completed = 0
    paginator = client.get_paginator('list_assignments_for_hit')
    for a_page in paginator.paginate(HITId=hit_id, PaginationConfig={'PageSize': 100}):
        for a in a_page['Assignments']:
            if a['AssignmentStatus'] in ['Submitted', 'Approved', 'Rejected']:
                completed += 1
    return completed, total


def is_hit_completed(client: boto3.session.Session, hit_id: str) -> bool:
    """ Return True if the HIT is completed """
    completed, total = get_hit_progress(client, hit_id)
    return completed == total


def progress_hits(client: boto3.session.Session, hits: List[str]) -> None:

    all_completed, all_total = 0, 0

    for hit in hits:
        completed, total = get_hit_progress(client, hit)
        all_completed += completed
        all_total += total
        logging.info(f"{hit}: {completed}/{total}")
        pbar = tqdm(total=total)
        pbar.update(completed)
        pbar.close()

def progress_recorded_hits(client: boto3.session.Session):
    """
    Return progress on the execution of the HITs
    """
    logging.info('Retrieve all HITs')
    hits = list_recorded_hits(client)
    progress_hits(client, [i['HITId'] for i in hits])

def progress_all_hits(client: boto3.session.Session):
    """
    Return progress on the execution of the HITs
    """
    logging.info('Retrieve all HITs')
    hits = list_all_hits(client)
    progress_hits(client, [i['HITId'] for i in hits])


def send_bonus(client: boto3.session.Session,
               assignement: str,
               worker: str,
               amount: str,
               message: str):

    client.send_bonus(WorkerId=str(worker),
                      BonusAmount=str(amount),
                      AssignmentId=str(assignement),
                      Reason=message)
