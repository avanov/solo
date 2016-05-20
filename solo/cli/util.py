from pathlib import Path
from typing import Dict, Any

import yaml


def parse_app_config(path: str) -> Dict[str, Any]:
    with Path(path).open() as f:
        config = yaml.load(f.read())
        return config
