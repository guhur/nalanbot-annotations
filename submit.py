import logging
from typing import Dict, Any
from jinja2 import Environment, PackageLoader
import yaml
from connect import connect_mturk
from config import get_config


def generate_template(task: Dict[str, Any]) -> str:
    env = Environment(loader=PackageLoader('templates'))
    template = env.get_template(task['template'])
    return template.render()

def create_task(task: Dict[str, Any]) -> Dict[str, str]:
    mturk = connect_mturk()
    question = generate_template(task)
    config = get_config()

    new_hit = mturk.create_hit(Title=task['title'],
                               Description=task['description'],
                               Keywords=task['keywords'],
                               Reward=task['reward'],
                               MaxAssignments=task['max_assignements'],
                               LifetimeInSeconds=task['liftetime'],
                               AssignmentDurationInSeconds=task['assignement_duration'],
                               AutoApprovalDelayInSeconds=task['auto_approval_delay'],
                               Question=question)

    preview_url = config['mturk']['preview_url'] + new_hit['HIT']['HITId']
    hit_id = new_hit['HIT']['HITGroupId']

    logging.info("A new HIT has been created.")
    logging.info(f"Preview: {preview_url}")
    logging.info(f"HIT Id {hit_id}")

    return {'preview': preview_url, 'id': hit_id}


if __name__ == "__main__":

    tasks = get_config('tasks')
    hit = []

    for task in tasks:
        hit.append(create_task(task))

    try:
        with open('hit.yaml', 'w') as ymlfile:
            yaml.dump(hit, ymlfile, default_flow_style=False)
    except yaml.YAMLError as err:
        logging.error(err)
