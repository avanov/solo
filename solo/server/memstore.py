import asyncio
from typing import Awaitable

import aioredis

from ..config.app import Config


def init_pool(loop: asyncio.AbstractEventLoop,
              config: Config) -> Awaitable[aioredis.commands.Redis]:
    c = config.redis
    address = (c.host, c.port)
    pool = aioredis.create_redis_pool(
        address=address,
        db=c.db,
        password=None,
        ssl=None,
        encoding=None,
        minsize=c.min_connections,
        maxsize=c.max_connections,
        loop=loop
    )
    return pool
