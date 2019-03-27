import logging

from .config.routes import Route
from .exceptions import ConfigurationError

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
            view_item = scanner.configurator.views.add_view(view=obj, **settings)
            namespace = scanner.configurator.router.namespace
            try:
                routes_namespace = scanner.configurator.router.routes[namespace]
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
            renderer = scanner.configurator.rendering.get_renderer(view_item.renderer)
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
