import logging
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
import yaml
from aws import connect_mturk, list_bucket_objects
from config import get_config
from generators import step_by_step_generator, description_generator, check_generator


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def generate_template(task: Dict[str, Any],
                      sample: Dict[str, str]) -> str:
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(task['template'])
    return template.render(**sample)


def create_job(client: Any,
               task: Dict[str, Any],
               sample: Dict) -> Dict[str, str]:
    question = generate_template(task, sample)
    config = get_config()

    new_hit = client.create_hit(Title=task['title'],
                                Description=task['description'],
                                Keywords=task['keywords'],
                                Reward=str(task['reward']),
                                MaxAssignments=task['max_assignements'],
                                LifetimeInSeconds=task['lifetime'],
                                AssignmentDurationInSeconds=task['assignement_duration'],
                                AutoApprovalDelayInSeconds=task['auto_approval_delay'],
                                Question=question)

    preview_url = config['mturk']['preview_url'] + new_hit['HIT']['HITGroupId']
    hit_id = new_hit['HIT']['HITId']

    logging.info("A new HIT has been created.")
    logging.info(f"Preview: {preview_url}")
    logging.info(f"HIT Id {hit_id}")

    return {**new_hit['HIT'], **sample}


if __name__ == "__main__":

    config = get_config()
    tasks = config['tasks']
    jobs = []

    client = connect_mturk()

    for task in tasks:
        logging.info(f"Submitting task {task['name']}")
        if task['name'] == "stepbystep":
            generator = step_by_step_generator
        elif task['name'] == "description":
            generator = description_generator
        elif task['name'] == "check":
            generator = check_generator
        else:
            raise ValueError(f"Unknown {task['name']}")

        for sample in generator(client, task):
            job = create_job(client, task, sample)
            jobs.append(job)

    logging.info("All tasks were successfully submitted.")
    logging.info(f"Information is recorded in {config['job_filename']}.")

    try:
        with open(config['job_filename'], 'a') as ymlfile:
            yaml.dump(jobs, ymlfile, default_flow_style=False)
    except yaml.YAMLError as err:
        logging.error(err)
