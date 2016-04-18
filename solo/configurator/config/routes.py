import os
from collections import OrderedDict
from typing import List, Optional
import logging

from ..exceptions import ConfigurationError


log = logging.getLogger(__name__)


class RoutesConfigurator:
    def __init__(self, route_prefix: str):
        self.route_prefix = route_prefix
        self.namespace = 'solo'
        self.routes = OrderedDict()
        self.routes[self.namespace] = OrderedDict()

    def change_route_prefix(self, prefix: str) -> str:
        old_prefix = self.route_prefix
        self.route_prefix = prefix
        return old_prefix

    def change_namespace(self, new: str) -> str:
        old = self.namespace
        self.namespace = new
        self.routes.setdefault(new, OrderedDict())
        return old

    def add_route(self, name: str, pattern: str, rules=None, extra_kwargs=None):
        pattern = os.path.join(self.route_prefix, pattern.strip('/')).rstrip('/')
        if not pattern:
            pattern = '/'

        if name in self.routes[self.namespace]:
            raise ConfigurationError('Route named "{}" is already registered in the namespace {}'.format(
                name, self.namespace
            ))

        log.debug('Registering global route "{pattern}" with the local name "{name}" in the {namespace} namespace'.format(
            pattern=pattern,
            name=name,
            namespace=self.namespace
        ))
        self.routes[self.namespace][name] = Route(name=name,
                                                  pattern=pattern,
                                                  rules=rules,
                                                  extra_kwargs=extra_kwargs,
                                                  viewlist=[])

    def check_routes_consistency(self, package):
        namespace = package.__name__
        log.debug('Checking routes consistency for {}...'.format(namespace))
        for route_name, route in self.routes[namespace].items():
            viewlist = route.viewlist
            if not viewlist:
                raise ConfigurationError(
                    'Route name "{name}" is not associated with a view callable in the {namespace} namespace.'.format(
                        name=route_name,
                        namespace=namespace
                    )
                )
            for view_item in viewlist:
                if view_item.view is None:
                    raise ConfigurationError(
                        'Route name "{name}" is not associated with a view callable in the {namespace} namespace.'.format(
                            name=route_name,
                            namespace=namespace
                        )
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
