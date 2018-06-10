import asyncio
from typing import Dict, Any
import aioredis
from aioredis.abc import AbcPool


async def init_pool(loop: asyncio.AbstractEventLoop,
                    config: Dict[str, Any]) -> AbcPool:
    c = config['redis']
    address = (c['host'], c['port'])
    pool = await aioredis.create_pool(address=address,
                                      db=c['db'],
                                      password=None,
                                      ssl=None,
                                      encoding=None,
                                      minsize=c['min_connections'],
                                      maxsize=c['max_connections'],
                                      loop=loop)
    return pool
