import logging
from typing import NamedTuple, Awaitable

import routes
import aioredis

from solo.server.db import SQLEngine

logger = logging.getLogger(__name__)


class App(NamedTuple):
    route_map: routes.Mapper
    url_gen: routes.URLGenerator
    dbengine: Awaitable[SQLEngine]
    memstore: Awaitable[aioredis.commands.Redis]
