import asyncio
import logging
from typing import Awaitable

import sqlalchemy as sa

from solo.config.app import Config
from .types import SQLEngine
from ...types import IO

log = logging.getLogger(__name__)


def setup_database(loop: asyncio.AbstractEventLoop,
                    config: Config) -> IO[SQLEngine]:
    """ Configure and return sqlalchemy's Engine instance with a
    built-in connection pool.
    """
    log.debug(f'Configuring PostgreSQL client {config.postgresql.port}...')
    dbconf = config.postgresql
    dsn = "dbname={dbname} user={user} password={password} host={host} port={port}".format(
        user=dbconf.user,
        password=dbconf.password,
        host=dbconf.host,
        port=dbconf.port,
        dbname=dbconf.dbname
    )
    engine = sa.create_engine(
        dsn=dsn,
        minsize=dbconf.min_connections,
        maxsize=dbconf.max_connections,
        loop=loop,
        echo=config.debug
    )
    return engine
