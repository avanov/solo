import logging
from typing import NamedTuple, Awaitable

import routes
from redis import asyncio as aioredis

from solo.server.db import SQLEngine
from solo.types import IO

logger = logging.getLogger(__name__)


class App(NamedTuple):
    route_map: routes.Mapper
    url_gen: routes.URLGenerator
    dbengine: IO[SQLEngine]
    memstore: IO[aioredis.Redis]
