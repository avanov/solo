from pathlib import Path
from typing import Dict, Any

import yaml


DEFAULT_CONFIG = {
    'debug': True,
    'server': {
        'host': '127.0.0.1',
        'port': '8000',
        'keep_alive': True,
    }
}


def parse_app_config(path: str) -> Dict[str, Any]:
    new_conf = DEFAULT_CONFIG.copy()
    with Path(path).open() as f:
        config = yaml.load(f.read())
        new_conf.update(config)
        return new_conf
