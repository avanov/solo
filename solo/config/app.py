from enum import Enum

from typing import NamedTuple, Dict, Sequence
from typeit import type_constructor


class AppConfig(NamedTuple):
    name: str
    url_prefix: str
    setup: Sequence[Dict] = []


class Session(NamedTuple):
    cookie_name: str
    cookie_secure: bool
    cookie_httponly: bool


class Redis(NamedTuple):
    host: str = '127.0.0.1'
    port: int = 6379
    db: int = 0
    min_connections: int = 1
    max_connections: int = 10


class Postgresql(NamedTuple):
    user: str = 'solo'
    dbname: str = 'solo'
    password: str = 'solo'
    host: str = '127.0.0.1'
    port: int = 5432
    min_connections: int = 1
    max_connections: int = 10


class EventLoopType(Enum):
    ASYNCIO = 'asyncio'
    UVLOOP = 'uvloop'


class Server(NamedTuple):
    public_uri: str = 'http://127.0.0.1:8000'
    host: str = '127.0.0.1'
    port: int = 8000
    keep_alive: bool = True
    # asyncio/uvloop
    event_loop: EventLoopType = EventLoopType.ASYNCIO


class Testing(NamedTuple):
    docker_pull: bool = True
    """ Pull images from registry if they are not available locally yet
    """


class Config(NamedTuple):
    server: Server
    session: Session
    apps: Sequence[AppConfig] = []
    logging: Dict = {'version': 1}
    debug: bool = True
    postgresql: Postgresql = Postgresql()
    redis: Redis = Redis()
    testing: Testing = Testing()


mk_config, dict_config = type_constructor(Config)