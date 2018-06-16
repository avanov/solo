from typing import NamedTuple, Dict, Sequence


class Config(NamedTuple):
    debug: bool = True
    server: Dict = {}
    session: Dict = {}
    apps: Sequence[Dict] = []
    logging: Dict = {'version': 1}
    redis: Dict = {}
    postgresql: Dict = {}
