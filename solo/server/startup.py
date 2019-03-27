import asyncio
import logging

import aiohttp_session
from aiohttp import web
from aiohttp_session.redis_storage import RedisStorage

from solo import Configurator
from solo.configurator import ApplicationManager
from solo.configurator.exceptions import ConfigurationError
from solo.configurator.registry import Registry
from solo.configurator.url import complete_route_pattern
from solo.configurator.view import PredicatedHandler
from solo.server import db
from solo.server import memstore
from solo.config.app import Config


log = logging.getLogger(__name__)


async def init_webapp(loop: asyncio.AbstractEventLoop,
                      config: Config) -> ApplicationManager:
    webapp = web.Application(loop=loop,
                             debug=config.debug)

    configurator = Configurator(webapp, config=config)

    for app in config.apps:
        log.debug("------- Setting up {} -------".format(app.name))
        configurator.include(app.name, app.url_prefix)
        configurator.scan(package=app.name, ignore=['.__pycache__', f'{app.name}.migrations'])
        webapp = register_routes(app.name, webapp, configurator)
        for setup_step in app.setup:
            directive, kw = list(setup_step.items())[0]
            getattr(configurator, directive)(**kw)


    # Setup database connection pool
    # ------------------------------
    try:
        engine = await db.setup_database(loop, config)
    except ConfigurationError as e:
        log.warning(f"{e}: you won't be able to use PostgresSQL in this instance.")
    else:
        setattr(webapp, 'dbengine', engine)

    # Setup memory store
    # ------------------
    memstore_pool = await memstore.init_pool(loop, config)
    setattr(webapp, 'memstore', memstore_pool)

    # Setup sessions middleware
    # -------------------------
    aiohttp_session.setup(webapp, RedisStorage(memstore_pool,
                                               cookie_name=config.session.cookie_name,
                                               secure=config.session.cookie_secure,
                                               httponly=config.session.cookie_httponly))

    return configurator.final_application()


def register_routes(namespace: str, webapp: web.Application, configurator: Configurator) -> web.Application:
    # app.router.add_route("GET", "/probabilities/{attrs:.+}",
    #                     probabilities.handlers.handler)
    # Setup routes
    # ------------
    application_routes = configurator.router.routes[namespace]
    for route in application_routes.values():
        handler = PredicatedHandler(route.rules, route.view_metas)
        guarded_route_pattern = complete_route_pattern(route.pattern, route.rules)
        log.debug('Binding route {} to the handler named {} in the namespace {}.'.format(
            guarded_route_pattern, route.name, namespace
        ))
        webapp.router.add_route(method='*',
                                path=guarded_route_pattern,
                                name=route.aiohttp_name,
                                handler=handler)
    return webapp
