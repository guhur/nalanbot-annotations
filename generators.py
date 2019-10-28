from typing import Any, Union, Callable
from pathlib import Path
import json
import csv
from aws import list_bucket_objects
from config import get_config


def step_by_step_generator(client=None) -> Any:
    """ A sample generator for the step by step experiment """

    config = get_config()
    dataset_folder = Path(config['dataset_folder'])
    s3_url = f"https://{config['bucket-name']}.s3.amazonaws.com/"

    if not dataset_folder.is_dir():
        raise ValueError(f"{dataset_folder} is not a folder")

    for first_name in dataset_folder.glob("*_first.jpg"):
        first_name = str(first_name.name)
        last_name = first_name[:-len("_first.jpg")] + "_last.jpg"
        num_simu = first_name.split("_")[-2]
        before = s3_url + first_name
        after = s3_url + last_name
        yield {'before': before, 'after': after, 'id': num_simu}


def check_generator(client) -> Any:
    """ A sample generator for the check experiment """

    config = get_config()
    dataset_folder = Path(config['dataset_folder'])
    s3_url = f"https://{config['bucket-name']}.s3.amazonaws.com/"
    annotation_file = Path(config['dataset_folder']) / "annotations.json"

    with open(annotation_file, 'r') as fid:
        annotations = json.load(fid)

    for annotation in annotations:
        image = s3_url + "tower_" + annotation['num_cubes'] + "_" + \
                annotation['id'] + "_first.jpg"
        yield {'instruction': annotation['instruction'],
               'id': annotation['id'],
               'image': image}


def description_generator(client) -> Any:
    """ A sample generator for the description experiment """

    config = get_config()
    dataset_folder = Path(config['dataset_folder'])
    s3_url = f"https://{config['bucket-name']}.s3.amazonaws.com/"

    if not dataset_folder.is_dir():
        raise ValueError(f"{dataset_folder} is not a folder")

    for last_name in dataset_folder.glob("*_last.jpg"):
        last_name = str(last_name.name)
        num_simu = last_name.split("_")[-2]
        after = s3_url + last_name
        yield {'image': after, 'id': num_simu}


def csv_generator(client, filename: Union[str, Path],
                  delimiter=";") -> Any:

    with open(filename, "r", newline="") as fid:
        reader = csv.reader(fid, delimiter=delimiter)
        header = next(reader)
        for row in reader:
            yield {key: value for key, value in zip(header, row)}


def retrieve_generator(name: str) -> Callable:
    if name == "stepbystep":
        generator = step_by_step_generator
    elif name == "description":
        generator = description_generator
    elif name == "check":
        generator = check_generator
    else:
        raise ValueError(f"Unknown {name}")
    return generator
