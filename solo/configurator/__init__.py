""" A large portion of this sub-package is taken from Pyramid

"""
import inspect
import logging
import pkgutil
from typing import Optional
from types import ModuleType

from aiohttp.web import Application
import ramlfications as raml
import venusian

from ..server.config import Config
from .util import maybe_dotted
from .config.rendering import BUILTIN_RENDERERS
from .config.rendering import RenderingConfigurator
from .config.routes import RoutesConfigurator
from .config.views import ViewsConfigurator
from .config.sums import SumTypesConfigurator
from .exceptions import ConfigurationError
from .path import caller_package
from .view import http_defaults
from .view import http_endpoint
from .url import normalize_route_pattern

__all__ = ['http_endpoint', 'http_defaults', 'Configurator']


log = logging.getLogger(__name__)


class ApplicationManager:
    def __init__(self, app: Application) -> None:
        self.app = app
        self.config: Config = app['config']
        self.loop = app.loop
        self.handler = app.make_handler(
            debug=self.config.debug,
            keep_alive_on=self.config.server.keep_alive
        )
        self.server = None

    def create_server(self, host: Optional[str] = None, port: Optional[int] = None, ssl: Optional[bool] = None):
        log.debug('Creating a new web server...')
        self.server = self.loop.run_until_complete(self.create_server_future(host, port, ssl))

    def create_server_future(self, host: Optional[str] = None, port: Optional[int] = None, ssl: Optional[bool] = None):
        """ Used in conftest
        """
        if host is None:
            host = self.config.server.host
        if port is None:
            port = self.config.server.port
        return self.loop.create_server(self.handler, host, port, ssl=ssl)

    def __enter__(self):
        log.debug('Entering application context...')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug('Exiting application context...')
        if hasattr(self.app, 'dbengine'):
            log.debug('Closing database connections...')
            self.app.dbengine.terminate()
            self.loop.run_until_complete(self.app.dbengine.wait_closed())

        # Close memstore pool
        if hasattr(self.app, 'memstore'):
            log.debug('Closing memory store connections...')
            self.loop.run_until_complete(self.app.memstore.clear())


        if self.server:
            log.debug('Stopping server...')
            self.server.close()
            self.loop.run_until_complete(self.server.wait_closed())

        log.debug('Shutting down the application...')
        self.loop.run_until_complete(self.app.shutdown())
        self.loop.run_until_complete(self.handler.finish_connections(60.0))
        self.loop.run_until_complete(self.app.cleanup())


class Configurator:
    venusian = venusian
    inspect = inspect

    def __init__(self,
                 app: Application,
                 route_prefix=None,
                 registry=None,
                 router_configurator=RoutesConfigurator,
                 views_configurator=ViewsConfigurator,
                 rendering_configurator=RenderingConfigurator,
                 sum_types_configurator=SumTypesConfigurator) -> None:
        if route_prefix is None:
            route_prefix = ''
        if registry is None:
            registry = {}

        self.app = app
        self.router = router_configurator(app, route_prefix)
        self.views = views_configurator(app)
        self.rendering = rendering_configurator(app)
        self.sums = sum_types_configurator(app)
        self._directives = {}
        self.registry = registry
        self.setup_configurator()

    def include(self, callable, route_prefix: Optional[str] = None):
        """
        :param callable: package to be configured
        :param route_prefix:
        :return:
        """
        configuration_section = maybe_dotted(callable)  # type: ModuleType
        old_namespace = self.router.change_namespace(configuration_section.__package__)

        module = self.inspect.getmodule(configuration_section)
        if module is configuration_section:
            try:
                configuration_section = getattr(module, 'includeme')
                log.debug('Including {}'.format(callable))
            except AttributeError:
                raise ConfigurationError(
                    "module {} has no attribute 'includeme'".format(module.__name__)
                )

        sourcefile = self.inspect.getsourcefile(configuration_section)

        if sourcefile is None:
            raise ConfigurationError(
                'No source file for module {} (.py file must exist, '
                'refusing to use orphan .pyc or .pyo file).'.format(module.__name__)
            )

        if route_prefix is None:
            route_prefix = ''
        route_prefix = u'{}/{}'.format(self.router.route_prefix.rstrip('/'), route_prefix.lstrip('/'))
        old_route_prefix = self.router.change_route_prefix(route_prefix)

        configuration_section(self)
        self.router.change_namespace(old_namespace)
        self.router.change_route_prefix(old_route_prefix)

    def include_api_specs(self, pkg_name: str, path: str):
        log.debug('Including API specs: {}:{}'.format(pkg_name, path))
        data = pkgutil.get_data(pkg_name, path)  # type: bytes
        data = data.decode('utf-8')
        data = raml.loads(data)
        raml_config = raml.setup_config(None)
        raml_config["validate"] = True
        specs = raml.parse_raml(data, raml_config)
        processed = set()
        for res in specs.resources:
            if res.name in processed:
                continue
            if not res.method:
                continue
            name, pattern, rules = normalize_route_pattern(res.path)
            self.router.add_route(name=name, pattern=pattern, rules=rules)
            processed.add(res.name)

    def scan(self, package=None, categories=None, onerror=None, ignore=None):
        if package is None:
            package = caller_package()
        package = maybe_dotted(package)
        log.debug('Scanning {}'.format(package))
        scanner = self.venusian.Scanner(config=self)
        previous_namespace = scanner.config.router.change_namespace(package.__name__)
        scanner.scan(package, categories=categories, onerror=onerror, ignore=ignore)
        self.router.check_routes_consistency(package)
        self.sums.check_sum_types_consistency(package)
        scanner.config.router.change_namespace(previous_namespace)
        log.debug('End scanning {}'.format(package))

    def setup_configurator(self):
        # Add default renderers
        # ---------------------
        for name, renderer in BUILTIN_RENDERERS.items():
            self.rendering.add_renderer(name, renderer)

        # Predicates machinery
        # --------------------
        self.views.add_default_view_predicates()


    def add_directive(self, directive, name=None, action_wrap=True):
        """ THIS METHOD IS A MODIFIED COPY OF ``pyramid.config.Configurator.add_directive``.
        MODIFIED ON: 2016-04-26.

        DOCS: http://docs.pylonsproject.org/projects/pyramid/en/latest/api/config.html#pyramid.config.Configurator.add_directive
        """
        c = maybe_dotted(directive)
        if name is None:
            name = c.__name__
        self._directives[name] = (c, action_wrap)


    def __getattr__(self, name: str):
        """ THIS METHOD IS A MODIFIED COPY OF ``pyramid.config.Configurator.__getattr__``.
        MODIFIED ON: 2016-04-26.
        """
        directives = getattr(self, '_directives', {})
        c = directives.get(name)
        if c is None:
            log.debug(directives)
            raise AttributeError(name)
        c, action_wrap = c
        # Create a bound method (works on both Py2 and Py3)
        # http://stackoverflow.com/a/1015405/209039
        m = c.__get__(self, self.__class__)
        return m

    def final_application(self) -> ApplicationManager:
        self.app.update(self.registry._asdict())
        self.app.update()
        return ApplicationManager(self.app)
