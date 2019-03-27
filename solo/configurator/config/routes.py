import os
from collections import OrderedDict
from dataclasses import dataclass
from types import ModuleType
from typing import List, Optional, Dict, NamedTuple, Any
import logging

import routes

from ..exceptions import ConfigurationError
from .sums import SumType


log = logging.getLogger(__name__)


class RoutesConfigurator:
    def __init__(self, url_gen: routes.URLGenerator, route_prefix: str):
        self.url_gen: routes.URLGenerator = url_gen
        self.route_prefix = route_prefix
        self.namespace = 'solo'
        self.routes: Dict[str, Dict[str, Route]] = OrderedDict()
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

    def add_route(self, name: str, pattern: str, rules: Optional[Dict[str, SumType]] = None, extra_kwargs=None):
        pattern = os.path.join(self.route_prefix, pattern.strip('/')).rstrip('/')
        if not pattern:
            pattern = '/'

        if rules is None:
            rules = {}

        if name in self.routes[self.namespace]:
            raise ConfigurationError(
                f'Route named "{name}" is already registered in the namespace {self.namespace}'
            )

        log.debug(
            f'Registering global route "{pattern}" '
            f'with the local name "{name}" in the {self.namespace} namespace'
        )
        self.routes[self.namespace][name] = Route(name=name,
                                                  pattern=pattern,
                                                  rules=rules,
                                                  extra_kwargs=extra_kwargs,
                                                  view_metas=[])

    def check_routes_consistency(self, package: ModuleType) -> None:
        namespace = package.__name__
        log.debug(f'Checking routes consistency for {namespace}...')
        for route_name, route in self.routes[namespace].items():
            view_metas = route.view_metas
            if not view_metas:
                raise ConfigurationError(
                    'Route name "{name}" is not associated with a view callable in the {namespace} namespace.'.format(
                        name=route_name,
                        namespace=namespace
                    )
                )
            for view_item in view_metas:
                if view_item.view is None:
                    raise ConfigurationError(
                        'Route name "{name}" is not associated with a view callable in the {namespace} namespace.'.format(
                            name=route_name,
                            namespace=namespace
                        )
                    )
    def url_for(self, ns: str, name: str, *args, **kwargs) -> str:
        return self.url_gen(f'{ns}:{name}', *args, **kwargs)


class ViewMeta:
    __slots__ = ['route_name', 'view', 'attr', 'renderer', 'predicates']

    def __init__(self, route_name: str, view, attr: Optional[str], renderer: str, predicates):
        self.route_name = route_name
        self.view = view
        self.attr = attr
        self.renderer = renderer
        self.predicates = predicates


class Route(NamedTuple):
    name: str
    pattern: str
    rules: Any
    extra_kwargs: Any
    view_metas: List[ViewMeta]
