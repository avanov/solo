import logging
from typing import List
from .config.routes import RouteItem
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
            scanner.config.add_view(view=obj, **settings)

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
    __slots__ = ['viewlist']

    def __init__(self, viewlist: List[RouteItem]):
        self.viewlist = viewlist

    async def __call__(self, request: Request):
        """ Resolve predicates here.
        """
        # here predicate is an instance object
        for route_item in self.viewlist:
            for predicate in route_item.predicates:
                if not predicate(None, request):
                    log.debug('Predicate {} failed for {} {}'.format(predicate, request.method, request.path_qs))
                    break
            else:
                # All predicates match
                log.debug('{} {} will be handled by {}'.format(request.method, request.path_qs, route_item.view))
                handler = route_item.view
                if route_item.attr:
                    # handler is a coroutine method of a class
                    handler = getattr(handler(request), route_item.attr)
                    response = await handler()
                else:
                    # handler is a simple coroutine
                    response = await handler(request)

                if isinstance(response, Response):
                    # Do not process standard responses
                    return response
                renderer = route_item.renderer
                return renderer(request, response)

        log.debug('All predicates have failed for {} {}'.format(request.method, request.path_qs))
        raise HTTPNotFound()
