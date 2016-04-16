from collections import OrderedDict
from typing import List, Optional
import logging

from ..exceptions import ConfigurationError


log = logging.getLogger(__name__)


class RoutesConfigurator:
    def __init__(self, route_prefix: str):
        self.route_prefix = route_prefix
        self.routes = OrderedDict()

    def add_route(self, name: str, pattern, rules=None, extra_kwargs=None):
        log.debug('Adding route {}'.format(name))
        pattern = u'{}/{}'.format(self.route_prefix.rstrip('/'), pattern.lstrip('/'))
        self.routes[name] = Route(name=name,
                                  pattern=pattern,
                                  rules=rules,
                                  extra_kwargs=extra_kwargs,
                                  viewlist=[])

    def check_routes_consistency(self, package):
        log.debug('Checking routes consistency for {}...'.format(package))
        for route_name, route in self.routes.items():
            viewlist = route.viewlist
            if not viewlist:
                raise ConfigurationError(
                    'Route name "{name}" is not associated with a view callable.'.format(name=route_name)
                )
            for view_item in viewlist:
                if view_item.view is None:
                    raise ConfigurationError(
                        'Route name "{name}" is not associated with a view callable.'.format(name=route_name)
                    )


class ViewMeta:
    __slots__ = ['route_name', 'view', 'attr', 'renderer', 'predicates']

    def __init__(self, route_name: str, view, attr: Optional[str], renderer, predicates):
        self.route_name = route_name
        self.view = view
        self.attr = attr
        self.renderer = renderer
        self.predicates = predicates


class Route:
    __slots__ = ['name', 'pattern', 'rules', 'extra_kwargs', 'viewlist']

    def __init__(self, name: str, pattern, rules, extra_kwargs, viewlist: List[ViewMeta]):
        self.name = name
        self.pattern = pattern
        self.rules = rules
        self.extra_kwargs = extra_kwargs
        self.viewlist = viewlist
