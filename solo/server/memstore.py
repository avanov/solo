import asyncio
from typing import Awaitable

import aioredis
from aioredis.abc import AbcPool

from ..config.app import Config


def init_pool(loop: asyncio.AbstractEventLoop,
              config: Config) -> Awaitable[AbcPool]:
    c = config.redis
    address = (c.host, c.port)
    pool = aioredis.create_pool(
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
