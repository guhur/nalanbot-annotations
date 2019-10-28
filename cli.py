#!/usr/bin/env python3
from typing import Union, List, Optional, Callable
import logging
import csv
import click
import aws
from config import get_config
from submit import is_job_in_records, create_job
from generators import retrieve_generator, csv_generator
from dataset import extract_ground_truth, generate_check_file

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


@cli.command("ground-truth", help="Retrieve ground truth")
@click.argument('csv-file',
                type=str)
@click.argument('dataset',
                type=str)
def ground_truth(csv_file: str, dataset: str):
    rows = []
    with open(csv_file, 'r', newline='') as fid:
        header = next(fid).split(',')
        reader = csv.reader(fid, delimiter=',')
        for row in reader:
            ground_truth = extract_ground_truth(dataset, row[0], row[1])
            row.append(ground_truth)
            rows.append(row)

    with open(csv_file, 'w', newline='') as fid:
        writer = csv.writer(fid, delimiter=',')
        for row in rows:
            writer.writerow(row)


@cli.command("check-generator", help="Generate data for the check step")
@click.argument('csv-file',
                type=str)
@click.argument('output',
                type=str)
def check_generator(csv_file: str, output: str):
    generate_check_file(csv_file, output)


@cli.command("bonus", help='Send bonus')
@click.option('--from-csv',
              default=None,
              help="Send bonus to all hits in the CSV result file")
@click.option('--amount',
              default=0.01,
              help="Amount to send")
@click.option('--message',
              default='Your answer is really helpful for our research! Hoping to get more answers from you!')
@click.option('--output',
              default='',
              help='Output CSV file to register the bonus')
def bonus(from_csv: Optional[str] = None,
          amount: float = 0.,
          message: str = "",
          output: str = ""):

    client = aws.connect_mturk()
    assignments = []
    workers = []
    done = []

    if output != "":
        with open(output, 'r', newline='') as fid:
            reader = csv.reader(fid, delimiter=',')
            for row in reader:
                done.append(row[0])

    if from_csv is not None:
        with open(from_csv, 'r', newline='') as fid:
            header = next(fid).split(',')
            reader = csv.reader(fid, delimiter=',')
            for row in reader:
                row_dict = {k: v for k, v in zip(header, row)}
                assignment_id = row_dict['assignment_id']

                if assignment_id in done:
                    continue

                if assignment_id not in assignments:
                    assignments.append(assignment_id)
                    workers.append(row_dict['worker_id'])
    else:
        raise ValueError("No job to reward")

    for assignment, worker in zip(assignments, workers):
        aws.send_bonus(client, assignment, worker, amount, message)

    if output != "":
        with open(output, 'a', newline='') as fid:
            writer = csv.writer(fid, delimiter=',')
            for assignment, worker in zip(assignments, workers):
                writer.writerow(assignment, worker, amount, message)


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
