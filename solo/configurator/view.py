import logging
from typing import List, Dict
from .config.routes import ViewMeta
from .config.routes import Route
from .config.sums import SumType
from .exceptions import ConfigurationError
from aiohttp.web import Request, Response, HTTPNotFound

import venusian


log = logging.getLogger(__name__)


class http_endpoint:
    venusian = venusian

    def __init__(self, **settings):
        self.__dict__.update(settings)

    def __call__(self, wrapped):
        settings = self.__dict__.copy()
        depth = settings.pop('_depth', 0)

        def callback(scanner, name, obj):
            view_item = scanner.config.views.add_view(view=obj, **settings)
            namespace = scanner.config.router.namespace
            try:
                routes_namespace = scanner.config.router.routes[namespace]
            except KeyError:
                raise ConfigurationError("Namespace was not included: {}".format(namespace))
            try:
                route = routes_namespace[view_item.route_name]  # type: Route
            except KeyError:
                raise ConfigurationError(
                    'No route named {route_name} found for view registration within {namespace} namespace.'.format(
                        route_name=view_item.route_name,
                        namespace=namespace
                    )
                )
            renderer = scanner.config.rendering.get_renderer(view_item.renderer)
            view_item.renderer = renderer
            route.view_metas.append(view_item)

        info = self.venusian.attach(wrapped, callback, category='solo', depth=depth + 1)
        if info.scope == 'class':
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # 'attr' into the settings if one isn't already in there
            if settings.get('attr') is None:
                settings['attr'] = wrapped.__name__
        return wrapped


class http_defaults(http_endpoint):
    """ This object is a copy of ``pyramid.view.view_defaults``.

    A class :term:`decorator` which, when applied to a class, will
    provide defaults for all view configurations that use the class. This
    decorator accepts all the arguments accepted by
    :meth:`pyramid.view.view_config`, and each has the same meaning.

    See :ref:`view_defaults` for more information.
    """
    def __call__(self, wrapped):
        wrapped.__view_defaults__ = self.__dict__.copy()
        return wrapped


class PredicatedHandler:
    __slots__ = ['rules', 'view_metas']

    def __init__(self, rules: Dict[str, SumType], view_metas: List[ViewMeta]):
        self.view_metas = view_metas
        self.rules = rules

    async def __call__(self, request: Request):
        """ Resolve predicates here.
        """
        # here predicate is an instance object
        for view_item in self.view_metas:
            for predicate in view_item.predicates:
                if not (await predicate(None, request)):
                    log.debug('Predicate {} failed for {} {}'.format(predicate, request.method, request.path_qs))
                    break
            else:
                # All predicates match
                log.debug('{} {} will be handled by {}'.format(request.method, request.path_qs, view_item.view))
                handler = view_item.view
                context = {}
                rules = self.rules
                for k, v in request.match_info.items():
                    if k in rules:  # match SumType's case
                        context[k] = self.rules[k].match(v)
                    else:  # regular value assignment
                        context[k] = v
                if view_item.attr:
                    # handler is a coroutine method of a class
                    handler = getattr(handler(request, context), view_item.attr)
                    response = await handler()
                else:
                    # handler is a simple coroutine
                    response = await handler(request, context)

                if isinstance(response, Response):
                    # Do not process standard responses
                    return response
                renderer = view_item.renderer
                return renderer(request, response)

        log.debug('All predicates have failed for {} {}'.format(request.method, request.path_qs))
        raise HTTPNotFound()
