from pathlib import Path

from solo.server.config import Config

import yaml


DEFAULT_CONFIG = {
    'debug': True,
    'server': {
        'host': '127.0.0.1',
        'port': '8000',
        'keep_alive': True,
    },
    'apps': [],
}


def parse_app_config(path: str) -> Config:
    new_conf = DEFAULT_CONFIG.copy()
    try:
        with Path(path).open() as f:
            config = yaml.load(f.read())
            new_conf.update(config)
            return Config(**new_conf)
    except FileNotFoundError:
        return Config()
