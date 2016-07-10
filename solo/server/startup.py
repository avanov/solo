import asyncio
import logging
from typing import Dict, Any

import aiohttp_session
from aiohttp import web
from aiohttp_session.redis_storage import RedisStorage

from solo import Configurator
from solo.configurator import ApplicationManager
from solo.configurator.url import complete_route_pattern
from solo.configurator.view import PredicatedHandler
from solo.server import db
from solo.server import memstore


log = logging.getLogger(__name__)


async def init_webapp(loop: asyncio.AbstractEventLoop,
                      config: Dict[str, Any]) -> ApplicationManager:
    webapp = web.Application(loop=loop,
                             debug=config['debug'])

    configurator = Configurator(webapp, registry={'config': config})

    apps = config['apps']
    for app_name, app_options in apps.items():
        log.debug("------- Setting up {} -------".format(app_name))
        configurator.include(app_name, app_options['url_prefix'])
        configurator.scan(package=app_name, ignore=['.__pycache__', '{}.migrations'.format(app_name)])
        webapp = register_routes(app_name, webapp, configurator)
        for setup_step in app_options.get('setup', []):
            directive, kw = list(setup_step.items())[0]
            getattr(configurator, directive)(**kw)


    # Setup database connection pool
    # ------------------------------
    engine = await db.setup_database(loop, config)
    setattr(webapp, 'dbengine', engine)

    # Setup memory store
    # ------------------
    memstore_pool = await memstore.init_pool(loop, config)
    setattr(webapp, 'memstore', memstore_pool)

    # Setup sessions middleware
    # -------------------------
    aiohttp_session.setup(webapp, RedisStorage(memstore_pool,
                                               cookie_name=config['session']['cookie_name'],
                                               secure=config['session']['cookie_secure'],
                                               httponly=config['session']['cookie_httponly']))

    return configurator.final_application()


def register_routes(namespace: str, webapp: web.Application, configurator: Configurator) -> web.Application:
    # app.router.add_route("GET", "/probabilities/{attrs:.+}",
    #                     probabilities.handlers.handler)
    # Setup routes
    # ------------
    application_routes = configurator.router.routes[namespace]
    for route in application_routes.values():  # type: Route
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