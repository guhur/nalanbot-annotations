from pathlib import Path
from typing import Any, Dict, Optional
import logging
import yaml


def get_config(sub: Optional[str] = None) -> Dict[str, Any]:
    """ find the config file with the biggest number """
    config_folder = Path() / "config"
    files = [f.stem for f in config_folder.glob("[0-9]*yaml")]
    priorities = [f.split(".")[0] for f in files]
    best_idx = max(enumerate(priorities), key=lambda x: x[1])[0]

    # load the config
    config_file = config_folder / (files[best_idx] + ".yaml")
    try:
        with open(config_file, 'r') as ymlfile:
            config = yaml.safe_load(ymlfile)
    except yaml.YAMLError as err:
        logging.error(err)

    return config if sub is None else config[sub]
