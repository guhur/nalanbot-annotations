import logging
import xmltodict
from connect import connect_mturk


def retrieve_hit(hit_id: str):
    mturk = connect_mturk()
    results = mturk.list_assignments_for_hit(HITId=hit_id,
                                             AssignmentStatuses=['Submitted'])

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
