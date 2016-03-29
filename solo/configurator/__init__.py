from collections import OrderedDict
from typing import Optional
import inspect
import logging

import pkg_resources
import venusian

from .config.rendering import RenderingConfiguratorMixin
from .config.rendering import BUILTIN_RENDERERS
from .config.routes import RoutesConfiguratorMixin
from .config.views import ViewsConfiguratorMixin
from .config.util import PredicateList
from .path import caller_package
from .exceptions import ConfigurationError
from .view import http_endpoint
from .view import http_defaults


__all__ = ['http_endpoint', 'http_defaults', 'Configurator']


log = logging.getLogger(__name__)


class Configurator(RoutesConfiguratorMixin,
                   ViewsConfiguratorMixin,
                   RenderingConfiguratorMixin):
    venusian = venusian
    inspect = inspect

    def __init__(self, route_prefix=None):
        if route_prefix is None:
            route_prefix = ''
        self.route_prefix = route_prefix

        self.routes = OrderedDict()
        self.renderers = {}
        # Predicates machinery
        # --------------------
        self.predicates = PredicateList()

        self.setup_registry()

    def include(self, callable, route_prefix: Optional[str] = None):
        if route_prefix is None:
            route_prefix = ''

        old_route_prefix = self.route_prefix
        route_prefix = u'{}/{}'.format(old_route_prefix.rstrip('/'), route_prefix.lstrip('/'))
        self.set_route_prefix(route_prefix)

        c = self.maybe_dotted(callable)
        module = self.inspect.getmodule(c)
        if module is c:
            try:
                c = getattr(module, 'includeme')
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

    def scan(self, package=None, categories=None, onerror=None, ignore=None):
        if package is None:
            package = caller_package()
        package = self.maybe_dotted(package)
        log.debug('Scanning {}'.format(package))
        scanner = self.venusian.Scanner(config=self)
        scanner.scan(package, categories=categories, onerror=onerror, ignore=ignore)
        self.check_routes_consistency()

    def get_predlist(self, name):
        """ This is a stub method that simply has the same signature as pyramid's version,
        but does nothing but returning ``self.predicates``
        """
        return self.predicates

    def setup_registry(self):
        # Add default renderers
        # ---------------------
        for name, renderer in BUILTIN_RENDERERS.items():
            self.add_renderer(name, renderer)

        self.add_default_view_predicates()

    def maybe_dotted(self, dotted):
        if not isinstance(dotted, str):
            return dotted
        return self._pkg_resources_style(dotted)

    def _pkg_resources_style(self, value):
        """ This method is taken from Pyramid Web Framework.

        package.module:attr style
        """
        # Calling EntryPoint.load with an argument is deprecated.
        # See https://pythonhosted.org/setuptools/history.html#id8
        ep = pkg_resources.EntryPoint.parse('x={}'.format(value))
        if hasattr(ep, 'resolve'):
            # setuptools>=10.2
            return ep.resolve()  # pragma: NO COVER
        else:
            return ep.load(False)  # pragma: NO COVER

    def _add_predicate(self, type, name, factory, weighs_more_than=None, weighs_less_than=None):
        """ This method is a highly simplified equivalent to what you can find in Pyramid.

        :param type: may be only 'view' at the moment
        :type type: str
        :param name: valid python identifier string.
        :type name: str
        :param weighs_more_than: not used at the moment
        :param weighs_less_than: not used at the moment
        """
        predlist = self.get_predlist(type)
        predlist.add(name, factory, weighs_more_than=weighs_more_than,
                     weighs_less_than=weighs_less_than)

    def set_route_prefix(self, prefix):
        self.route_prefix = prefix
