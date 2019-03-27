""" A large portion of this sub-package is taken from Pyramid

"""
import inspect
import logging
import pkgutil
from typing import Optional, Tuple
from types import ModuleType

import ramlfications as raml
import venusian
from pyrsistent import pmap, pvector

from solo.server.app import App
from solo.server.csrf import SessionCSRFStoragePolicy
from ..config.app import Config, AppConfig
from .util import maybe_dotted
from .config.rendering import BUILTIN_RENDERERS
from .config.rendering import RenderingConfigurator
from .config.routes import RoutesConfigurator
from .config.views import ViewsConfigurator
from .config.sums import SumTypesConfigurator
from .exceptions import ConfigurationError
from .registry import Registry
from .path import caller_package
from .view import http_defaults
from solo.server.definitions import PredicatedHandler
from .view import http_endpoint
from .url import normalize_route_pattern, complete_route_pattern, complete_url_rules

__all__ = ['http_endpoint', 'http_defaults', 'Configurator']


log = logging.getLogger(__name__)


class Configurator:
    venusian = venusian
    inspect = inspect

    def __init__(self,
                 app: App,
                 config: Config,
                 route_prefix=None,
                 router_configurator=RoutesConfigurator,
                 views_configurator=ViewsConfigurator,
                 rendering_configurator=RenderingConfigurator,
                 sum_types_configurator=SumTypesConfigurator) -> None:
        if route_prefix is None:
            route_prefix = ''
        self.app = app
        self.registry = Registry(config=config,
                                 csrf_policy=SessionCSRFStoragePolicy())
        self.router = router_configurator(app.url_gen, route_prefix)
        self.views = views_configurator(app)
        self.rendering = rendering_configurator(app)
        self.sums = sum_types_configurator()
        self._directives = pmap({})
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

    def scan(self, package: Optional[AppConfig] = None, categories=None, onerror=None, ignore=None) -> None:
        pkg_name = package.name if package else caller_package()
        pkg = maybe_dotted(pkg_name)

        log.debug(f'Scanning {pkg}')

        scanner = self.venusian.Scanner(configurator=self)

        previous_namespace = scanner.configurator.router.change_namespace(pkg.__name__)
        scanner.scan(pkg, categories=categories, onerror=onerror, ignore=ignore)
        self.router.check_routes_consistency(pkg)
        self.sums.check_sum_types_consistency(pkg)
        scanner.configurator.router.change_namespace(previous_namespace)

        self.app = self.register_routes(self.app, pkg_name)

        for setup_step in package.setup:
            directive, kw = pvector(setup_step.items())[0]
            getattr(self, directive)(**kw)
        log.debug(f'End scanning {pkg}')

    def register_routes(self, webapp: App, namespace: str) -> App:
        # Setup routes
        # ------------
        application_routes = self.router.routes[namespace]
        for route in application_routes.values():
            handler = PredicatedHandler(route.rules, route.view_metas)
            requirements = complete_url_rules(route.rules)
            log.debug(
                f'Binding route {route.pattern} '
                f'to the handler named {route.name} '
                f'in the namespace {namespace}.'
            )
            webapp.route_map.connect(
                f'{namespace}:{route.name}',
                route.pattern,
                requirements=requirements,
                controller=handler
            )
        return webapp

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
        self._directives = self._directives.update({name: (c, action_wrap)})


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

    def complete(self) -> Tuple[App, Registry]:
        return self.app, self.registry
