from pathlib import Path

from solo.config import app
from solo.config import docker_compose

import yaml


def parse_app_config(path: Path) -> app.Config:
    with path.open('r') as f:
        cfg = yaml.load(f.read(), Loader=yaml.FullLoader)
        return app.mk_config(cfg)


def parse_compose_config(path: Path) -> docker_compose.Config:
    with path.open('r') as f:
        cfg = yaml.load(f.read(), Loader=yaml.FullLoader)
        return docker_compose.mk_config(cfg)
