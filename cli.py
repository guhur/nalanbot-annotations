#!/usr/bin/env python3
from typing import Union, List, Optional, Callable
import logging
import click
import aws
from config import get_config
from submit import is_job_in_records, create_job
from generators import retrieve_generator, csv_generator

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@click.group()
def cli():
    pass

@cli.command("delete", help='Delete one or several HITs')
@click.option('--all-hits',
              default=False,
              is_flag=True,
              help="Delete all HITs related to account")
@click.option('--hit-id',
              default=None,
              help="Specific HITId",
              multiple=True)
def delete(all_hits: bool = False,
           hit_id: Optional[List[str]] = None):
    client = aws.connect_mturk()

    if all_hits:
        aws.delete_all_hits(client)
    elif hit_id is not None:
        for hit in hit_id:
            aws.delete_hit(client, hit)
    else:
        aws.delete_recorded_hits(client)


@cli.command("progress", help='Show progress')
@click.option('--all-hits',
              default=False,
              is_flag=True,
              help="Show progress on all HITs related to account")
@click.option('--all-recorded',
              default=False,
              is_flag=True,
              help="Show progress on all HITs recorded in local file")
@click.option('--hit-id',
              default=None,
              help="Specific HITId",
              multiple=True)
def progress(all_hits: bool = False,
             all_recorded: bool = False,
             hit_id: Optional[List[str]] = None):

    client = aws.connect_mturk()

    if all_hits:
        aws.progress_all_hits(client)
    elif all_recorded:
        aws.progress_recorded_hits(client)
    elif hit_id != tuple():
        aws.progress_hits(client, hit_id)
    else:
        raise ValueError("No job to delete")


@cli.command("submit", help='Submit one or several HITs')
@click.option('--allow-duplicate',
              default=False,
              is_flag=True,
              help="Allow that the same HIT is send several times")
@click.option('--name',
              default=None,
              help="Specific HITId",
              multiple=True)
@click.option('--all-tasks',
              default=False,
              is_flag=True,
              help="Submit all tasks")
@click.option('--from-csv',
              default=None,
              help="From CSV records")
def submit(allow_duplicate: bool = False,
           name: Optional[List[str]] = None,
           all_tasks: bool = False,
           from_csv: Optional[str] = None):

    if name == tuple() and not all_tasks:
        raise ValueError("No task to submit")

    client = aws.connect_mturk()

    config = get_config()
    tasks = config['tasks']

    if name != tuple():
        tasks = [task for task in tasks if task['name'] in name]

    for task in tasks:
        logging.info(f"Submitting task {task['name']}")

        if from_csv is None:
            generator_name = retrieve_generator(task['name'])
            generator = generator_name(client)
        else:
            generator = csv_generator(client, from_csv)

        for sample in generator:
            if not allow_duplicate \
                    and not is_job_in_records(task['name'], sample):
                create_job(client, task, sample)


if __name__ == "__main__":
    cli()
