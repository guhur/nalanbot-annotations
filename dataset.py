from typing import Union
from pathlib import Path
import json
import csv


def extract_ground_truth(dataset_folder: Union[Path, str],
                         num_cubes: int,
                         ref: int):
    """ Extract the sequence of colors """

    folder = Path(dataset_folder) / f"{int(num_cubes):02d}" / f"{int(ref):05d}"

    assert folder.is_dir(), f"Can't find {folder}"

    with open(folder / "annotation.json", "r") as fid:
        ground_truth = json.load(fid)

    return ground_truth['color']


def generate_check_file(csv_file: Union[Path, str],
                        output_file: Union[Path, str]):
    """ Extract the sequence of colors """

    assert Path(csv_file).is_file(), f"Can't find {csv_file}"

    annotations = []

    with open(csv_file, 'r', newline='') as fid:
        header = next(fid).split(',')
        reader = csv.reader(fid, delimiter=',')

        for row in reader:
            row_dict = {k: v for k, v in zip(header, row)}
            
            if row_dict['status'] in ['approved', 'to approve']:
                annotate = {'answer': row_dict['answer'],
                            'num_cubes': row_dict['numCubes'],
                            'ref': row_dict['ref']}

                annotations.append(annotate)

    with open(output_file, "w") as fid:
        for annotate in annotations:
            fid.write(json.dumps(annotate))
            fid.write('\n')
