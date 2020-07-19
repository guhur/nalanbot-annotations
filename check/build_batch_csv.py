from tempfile import TemporaryDirectory
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from pathlib import Path
from tqdm import tqdm
import argparse
import csv
from PIL import Image
import pymongo
import boto3
from botocore.exceptions import ClientError
from dacite import from_dict
import nalanbot as nb
from utils import *


@dataclass
class Sample:
    sentence: str
    state: nb.State
    _id: str
    url: str = ""


def load_samples(host: str, collection: str) -> List[Sample]:
    client = pymongo.MongoClient(host=args.host)
    col = client.nalanbot[args.collection]
    return [
        Sample(ds["sentence"], from_dict(nb.State, ds["states"][0]), ds["_id"])
        for ds in col.find()
    ]


def render_samples(samples: List[Sample], bucket_name: str) -> None:
    s3 = boto3.client("s3")
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        manager = nb.ExperimentManager(output_folder=tmppath)
        nb.supervised_default_params(manager)
        render = nb.render_init(manager)
        images = render([s.state for s in samples])

        for image, sample in zip(tqdm(images), samples):
            rgb, depth = image
            local_file = f"{sample._id}.png"
            Image.fromarray(rgb).save(tmppath / local_file)
            sample.url = f"https://{bucket_name}.s3.amazonaws.com/{local_file}"
            # s3.upload_file(str(tmppath / local_file), bucket_name, local_file)


def export_csv(filename: Path, samples: List[Sample]) -> None:
    rows = []
    num_samples = len(samples)
    index = list(range(num_samples))
    for subindex in index[::3]:
        row = {}
        max_index = min(len(index), subindex + 3)
        for i, sample_id in enumerate(range(subindex, max_index)):
            row[f"sentence{i}"] = samples[sample_id].sentence
            row[f"id{i}"] = samples[sample_id]._id
            row[f"url{i}"] = samples[sample_id].url
        rows.append(row)

    assert rows != []

    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())

        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", "-c", type=str, required=True)
    parser.add_argument("--bucket-name", "-b", type=str, required=True)
    parser.add_argument("--build", default=BUILD_FOLDER, type=Path)
    parser.add_argument("--host", default="localhost", type=str)
    args = parser.parse_args()

    samples = load_samples(args.host, args.collection)
    print(f"Found {len(samples)} samples")

    render_samples(samples, args.bucket_name)

    export_csv(args.build / f"batch-{args.bucket_name}", samples)
