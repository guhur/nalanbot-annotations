import logging
import xmltodict
import yaml
from aws import connect_mturk
from config import get_config


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def retrieve_job(job_id: str) -> None:
    mturk = connect_mturk()
    results = mturk.list_assignments_for_hit(HITId=job_id)

    if results['NumResults'] > 0:
        for assignment in results['Assignments']:
            xml_doc = xmltodict.parse(assignment['Answer'])

            logging.info("Worker's answer was:")
            if isinstance(xml_doc['QuestionFormAnswers']['Answer'], list):
                # Multiple fields in HIT layout
                for answer_field in xml_doc['QuestionFormAnswers']['Answer']:
                    logging.info("For input field: " + answer_field['QuestionIdentifier'])
                    logging.info("Submitted answer: " + answer_field['FreeText'])
            else:
                # One field found in HIT layout
                logging.info("For input field: " + xml_doc['QuestionFormAnswers']['Answer']['QuestionIdentifier'])
                logging.info("Submitted answer: " + xml_doc['QuestionFormAnswers']['Answer']['FreeText'])
    else:
        logging.info("No results ready yet")


if __name__ == "__main__":

    config = get_config()
    job = []

    try:
        with open(config['job_filename'], 'r') as ymlfile:
            jobs = yaml.safe_load(ymlfile)
    except yaml.YAMLError as err:
        logging.error(err)

    for job in jobs:
        logging.info(f"Retrieving job {job['name']}")
        retrieve_job(job['id'])
