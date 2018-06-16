import asyncio
import logging
from typing import Dict, Any
import aiopg.sa

from solo.configurator.exceptions import ConfigurationError
from solo.server.config import Config


log = logging.getLogger(__name__)


async def setup_database(loop: asyncio.AbstractEventLoop,
                         config: Config) -> aiopg.sa.Engine:
    """ Configure and return sqlalchemy's Engine instance with a
    built-in connection pool.
    """
    log.debug('Establishing connection with PostgreSQL...')
    try:
        dbconf = config.postgresql
    except KeyError:
        raise ConfigurationError('PostgreSQL configuration is not provided')

    dsn = "dbname={dbname} user={user} password={password} host={host} port={port}".format(
        user=dbconf['user'],
        password=dbconf['password'],
        host=dbconf['host'],
        port=dbconf['port'],
        dbname=dbconf['dbname']
    )
    engine = await aiopg.sa.create_engine(dsn=dsn,
                                          minsize=dbconf['min_connections'],
                                          maxsize=dbconf['max_connections'],
                                          loop=loop,
                                          echo=config.debug)
    return engine
