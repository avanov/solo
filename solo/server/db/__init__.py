import asyncio
import logging
from typing import Awaitable

import sqlalchemy as sa

from solo.config.app import Config
from .types import SQLEngine
from ...types import IO

log = logging.getLogger(__name__)


def setup_database(loop: asyncio.AbstractEventLoop,
                    config: Config) -> SQLEngine:
    """ Configure and return sqlalchemy's Engine instance with a
    built-in connection pool.
    """
    log.debug(f'Configuring PostgreSQL client {config.postgresql.port}...')
    db_conf = config.postgresql
    url = "postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}?sslmode=allow".format(
        user=db_conf.user,
        password=db_conf.password,
        host=db_conf.host,
        port=db_conf.port,
        dbname=db_conf.dbname
    )
    engine = sa.create_engine(
        url=url,
        pool_size=db_conf.min_connections,
        max_overflow=db_conf.max_connections,
        echo=config.debug
    )
    return engine
