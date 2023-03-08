import asyncio
import logging

import routes
from pyrsistent import pvector

from ..configurator import Configurator
from solo.server.io_manager import AIOManager
from solo.server import db
from solo.server import memstore
from solo.config.app import Config
from solo.server.app import App

log = logging.getLogger(__name__)


def application_entrypoint(loop: asyncio.AbstractEventLoop,
                          config: Config) -> AIOManager:
    """ This is where our web application starts from a config provided through CLI.
    """
    # Setup database connection pool
    # ------------------------------
    dbengine = db.setup_database(config)

    # Setup memory store
    # ------------------
    memstore_pool = memstore.init_pool(config)
    url_gen = routes.URLGenerator(
        routes.Mapper(),
        {'SERVER_NAME': config.server.host,
         'SERVER_PORT': config.server.port}
    )
    app = App(
        route_map=url_gen.mapper,
        url_gen=url_gen,
        db_engine=dbengine,
        memstore=memstore_pool,
    )
    configurator = Configurator(app, config=config)

    for user_app in config.apps:
        log.debug(f"------- Setting up {user_app.name} -------")
        configurator.include(user_app.name, user_app.url_prefix)
        configurator.scan(
            package=user_app,
            ignore=pvector(['.__pycache__', f'{user_app.name}.migrations'])
        )
    app, registry = configurator.complete()
    log.debug(f'Serving on http://{config.server.host}:{config.server.port}')
    return AIOManager ( loop     = loop
                      , app      = app
                      , registry = registry )
