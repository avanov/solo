import uuid
import asyncio
from typing import Any, Dict
import logging

from aiohttp import web

from . import db
from ..configurator import Configurator
from ..configurator.view import PredicatedHandler


log = logging.getLogger(__name__)


async def init_webapp(loop: asyncio.AbstractEventLoop,
                      config: Dict[str, Any]) -> web.Application:
    webapp = web.Application(loop=loop,
                             debug=config['debug'])

    configurator = Configurator()

    apps = config['apps']
    for app_name, app_options in apps.items():
        configurator.include(app_name, app_options['url_prefix'])
        configurator.scan(package=app_name, ignore=['.__pycache__'])

    webapp = register_routes(webapp, configurator)

    # Setup database connection pool
    # ------------------------------
    engine = await db.setup_database(loop, config)
    setattr(webapp, 'dbengine', engine)
    return webapp


def register_routes(webapp: web.Application, configurator: Configurator) -> web.Application:
    # app.router.add_route("GET", "/probabilities/{attrs:.+}",
    #                     probabilities.handlers.handler)
    # Setup routes
    # ------------
    for app_namespace, application_routes in configurator.router.routes.items():
        for route in application_routes.values():
            log.debug('Binding route {} to the handler named {} in the namespace {}.'.format(
                route.pattern, route.name, app_namespace
            ))
            handler = PredicatedHandler(route.viewlist)
            verbose_route_name = route.pattern.replace('/', '_').replace('{', '_').replace('}', '_')
            webapp.router.add_route(method='*',
                                    path=route.pattern,
                                    name=verbose_route_name,
                                    handler=handler)
    return webapp
