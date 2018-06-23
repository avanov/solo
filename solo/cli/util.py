from pathlib import Path

from solo.server import config

import yaml


def parse_app_config(path: str) -> config.Config:
    with Path(path).open('r') as f:
        cfg = yaml.load(f.read())
        return config.MakeConfig(cfg)