import asyncio
import logging
from typing import Mapping, Callable

import routes
from aiohttp import web
from pyrsistent import pvector, pmap
from pyrsistent.typing import PMap

from ..configurator import Configurator
from ..configurator import AIOManager
from ..configurator.url import complete_route_pattern
from ..configurator.view import PredicatedHandler
from solo.server import db
from solo.server import memstore
from solo.config.app import Config, RunnerType
from solo.server.app import App

log = logging.getLogger(__name__)


def application_entrypoint(loop: asyncio.AbstractEventLoop,
                           config: Config) -> AIOManager:
    """ This is where our web application starts from a config provided through CLI.
    """
    return RUNNERS[config.server.runner](loop, config)


def configure_aiohttp_app(loop: asyncio.AbstractEventLoop,
                          config: Config) -> AIOManager:
    solo_app = web.Application(loop=loop, debug=config.debug)

    configurator = Configurator(solo_app, config=config)

    for user_app in config.apps:
        log.debug(f"------- Setting up {user_app.name} -------")
        configurator.include(user_app.name, user_app.url_prefix)
        configurator.scan(
            package=user_app.name,

            ignore=pvector(['.__pycache__', f'{user_app.name}.migrations'])
        )
        solo_app = register_routes(user_app.name, solo_app, configurator)
        for setup_step in user_app.setup:
            directive, kw = pvector(setup_step.items())[0]
            getattr(configurator, directive)(**kw)


    # Setup database connection pool
    # ------------------------------
    engine = db.setup_database(loop, config)
    setattr(solo_app, 'dbengine', engine)

    # Setup memory store
    # ------------------
    memstore_pool = memstore.init_pool(loop, config)
    setattr(solo_app, 'memstore', memstore_pool)

    return configurator.complete()


def configure_uvicorn_app(loop: asyncio.AbstractEventLoop,
                          config: Config) -> AIOManager:
    # Setup database connection pool
    # ------------------------------
    dbengine = db.setup_database(loop, config)

    # Setup memory store
    # ------------------
    memstore_pool = memstore.init_pool(loop, config)

    app = App(
        route_map=routes.Mapper(),
        dbengine=dbengine,
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

    return configurator.complete()


RUNNERS: PMap[RunnerType, Callable] = pmap({
    RunnerType.AIOHTTP: configure_aiohttp_app,
    RunnerType.UVICORN: configure_uvicorn_app,
})
