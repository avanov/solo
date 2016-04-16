import inspect
import logging
import pkgutil
from typing import Optional

import ramlfications as raml
import venusian

from .util import maybe_dotted
from .config.rendering import BUILTIN_RENDERERS
from .config.rendering import RenderingConfigurator
from .config.routes import RoutesConfigurator
from .config.views import ViewsConfigurator
from .exceptions import ConfigurationError
from .path import caller_package
from .view import http_defaults
from .view import http_endpoint

__all__ = ['http_endpoint', 'http_defaults', 'Configurator']


log = logging.getLogger(__name__)


class Configurator:
    venusian = venusian
    inspect = inspect

    def __init__(self,
                 route_prefix=None,
                 router_configurator=RoutesConfigurator,
                 views_configurator=ViewsConfigurator,
                 rendering_configurator=RenderingConfigurator):
        if route_prefix is None:
            route_prefix = ''
        self.router = router_configurator(route_prefix)
        self.views = views_configurator()
        self.rendering = rendering_configurator()
        # Predicates machinery
        # --------------------

        self.setup_registry()

    def include(self, callable, route_prefix: Optional[str] = None):
        if route_prefix is None:
            route_prefix = ''

        old_route_prefix = self.router.route_prefix
        route_prefix = u'{}/{}'.format(old_route_prefix.rstrip('/'), route_prefix.lstrip('/'))
        self.set_route_prefix(route_prefix)

        c = maybe_dotted(callable)
        module = self.inspect.getmodule(c)
        if module is c:
            try:
                c = getattr(module, 'includeme')
                log.debug('Including {}'.format(callable))
            except AttributeError:
                raise ConfigurationError(
                    "module {} has no attribute 'includeme'".format(module.__name__)
                )

        sourcefile = self.inspect.getsourcefile(c)

        if sourcefile is None:
            raise ConfigurationError(
                'No source file for module {} (.py file must exist, '
                'refusing to use orphan .pyc or .pyo file).'.format(module.__name__)
            )

        c(self)
        self.set_route_prefix(old_route_prefix)

    def include_api_specs(self, package: str, path: str):
        log.debug('Including API specs: {}:{}'.format(package, path))
        data = pkgutil.get_data(package, path)  # type: bytes
        data = data.decode('utf-8')
        data = raml.loads(data)
        raml_config = raml.setup_config(None)
        raml_config["validate"] = True
        specs = raml.parse_raml(data, raml_config)
        for res in specs.resources:
            route = '{}/{}'.format(self.router.route_prefix.rstrip('/'), res.name.lstrip('/')).rstrip('/')
            log.debug('\tRegistering API resource: {}'.format(route))

    def scan(self, package=None, categories=None, onerror=None, ignore=None):
        if package is None:
            package = caller_package()
        package = maybe_dotted(package)
        log.debug('Scanning {}'.format(package))
        scanner = self.venusian.Scanner(config=self)
        scanner.scan(package, categories=categories, onerror=onerror, ignore=ignore)
        self.router.check_routes_consistency(package)
        log.debug('End scanning {}'.format(package))

    def setup_registry(self):
        # Add default renderers
        # ---------------------
        for name, renderer in BUILTIN_RENDERERS.items():
            self.rendering.add_renderer(name, renderer)

        self.views.add_default_view_predicates()

    def set_route_prefix(self, prefix):
        self.router.route_prefix = prefix
