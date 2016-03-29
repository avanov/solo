import asyncio
from typing import Any, Dict, Tuple

from aiohttp import web

from . import db
from ..configurator import Configurator


async def init_webapp(loop: asyncio.AbstractEventLoop,
                      config: Dict[str, Any]) -> web.Application:
    configurator = Configurator()
    #configurator.include('pacific.db')

    apps = get_apps_mapping(config)
    for app_name, url_prefix in apps.items():
        configurator.include(app_name, url_prefix)

    configurator.scan()
    # We must also scan applications' packages
    for app_name in apps:
        configurator.scan(app_name)

    webapp = web.Application(loop=loop,
                          debug=config['debug'])
    # Setup routes
    # ------------
    def generate_webapp(webapp: web.Application, configurator: Configurator) -> web.Application:
        #app.router.add_route("GET", "/probabilities/{attrs:.+}",
        #                     probabilities.handlers.handler)
        for route in configurator.routes.values():
            create_django_route(
                name=route.name,
                pattern=route.pattern,
                rules=route.rules,
                extra_kwargs=route.extra_kwargs,
                viewlist=route.viewlist
            )
            webapp.router.add_route('*', '/path/to', MyView)
        return webapp
    webapp = generate_webapp(webapp, configurator)

    # Setup database connection pool
    # ------------------------------
    engine = await db.setup_database(loop, config)
    setattr(webapp, 'dbengine', engine)
    return webapp


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """


def get_apps_mapping(config):
    """
    :param config:
    :type config: :class:`pyramid.config.Configurator`
    :return: mapping of app_name => app_url_prefix
    :rtype: dict
    """
    apps_list = config.registry.settings['apps'].split(' ')
    apps = {}
    for app_mapping in apps_list:
        app_name, url_prefix = app_mapping.split('=>', 1)
        apps[app_name] = url_prefix
    return apps
