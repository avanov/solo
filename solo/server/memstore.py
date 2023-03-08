import asyncio

from redis import asyncio as aioredis

from ..config.app import Config
from ..types import IO


def init_pool(config: Config) -> IO[aioredis.Redis]:
    c = config.redis
    pool = aioredis.Redis(
        host=c.host,
        port=c.port,
        db=c.db,
        password=None,
        max_connections=c.max_connections,
    )
    return pool
