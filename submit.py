import logging
from typing import Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import yaml
from aws import connect_mturk, list_bucket_objects
from config import get_config
from generators import retrieve_generator


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def generate_template(task: Dict[str, Any],
                      sample: Dict[str, str]) -> str:
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(task['template'])
    return template.render(**sample)



def is_job_in_records(task_name: str, sample: Dict[str, str]) -> bool:
    """ Check if we can find the job in the records """ 
    config = get_config()

    if not Path(config['job_filename']).is_file():
        return False

    with open(config['job_filename'], 'r') as ymlfile:
        jobs = yaml.safe_load(ymlfile)

    for job in jobs:
        if job is None:
            continue
        if not 'task_name' in job or job['task_name'] != task_name:
            continue
        if any([k in job.keys() for k in sample.keys()]):
            continue
        if all([job[key] == sample[key] for key in sample.keys()]):
            return True

    return False


def create_job(client: Any,
               task: Dict[str, Any],
               sample: Dict) -> Dict[str, str]:
    question = generate_template(task, sample)
    config = get_config()

    new_hit = client.create_hit(Title=task['title'],
                                Description=task['description'],
                                Keywords=task['keywords'],
                                Reward=str(task['reward']),
                                MaxAssignments=task['max_assignments'],
                                LifetimeInSeconds=task['lifetime'],
                                AssignmentDurationInSeconds=task['assignment_duration'],
                                AutoApprovalDelayInSeconds=task['auto_approval_delay'],
                                Question=question)

    preview_url = config['mturk']['preview_url'] + new_hit['HIT']['HITGroupId']
    hit_id = new_hit['HIT']['HITId']

    logging.info("A new HIT has been created.")
    logging.info(f"Preview: {preview_url}")
    logging.info(f"HIT Id {hit_id}")

    job = {**new_hit['HIT'], **sample, "task_name": task['name']}
    del job['Question']

    try:
        with open(config['job_filename'], 'a') as ymlfile:
            yaml.dump([job], ymlfile, default_flow_style=False)
    except yaml.YAMLError as err:
        logging.error(err)

    return job


def create_task(client: Any,
                task: Dict[str, Any]):

    config = get_config()

    response = client.create_hit_type(Title=task['title'],
                                      Description=task['description'],
                                      Keywords=task['keywords'],
                                      Reward=str(task['reward']),
                                      AssignmentDurationInSeconds=task['assignment_duration'],
                                      AutoApprovalDelayInSeconds=task['auto_approval_delay'])

    return response



if __name__ == "__main__":

    config = get_config()
    tasks = config['tasks']
    jobs = []

    client = connect_mturk()

    for task in tasks:
        logging.info(f"Submitting task {task['name']}")
        generator = retrieve_generator(task['name'])(client)

        for sample in generator:
            job = create_job(client, task, sample)
            jobs.append(job)

    logging.info("All tasks were successfully submitted.")
    logging.info(f"Information is recorded in {config['job_filename']}.")
