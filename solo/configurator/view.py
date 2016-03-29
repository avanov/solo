from aiohttp.web import Response
from django.http import Http404

import venusian


class http_endpoint(object):
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


class ViewCallback(object):
    """ Wrapper object around actual view callables that checks predicates during the request
    and processes results returned from view callables during the response.
    """
    def __init__(self, viewlist):
        self.viewlist = viewlist

    def __call__(self, request, *args, **kwargs):
        view_settings = self.find_view_settings(request, args, kwargs)
        response = view_settings['view'](request, *args, **kwargs)
        return self.process_callback_response(request, response, view_settings)

    def find_view_settings(self, request, args, kwargs):
        if hasattr(request, 'solo_view_settings'):
            return getattr(request, 'solo_view_settings')

        # cache
        for view_settings in self.viewlist:
            passed, request = self.check_predicates(view_settings, request, args, kwargs)
            if passed:
                setattr(request, 'solo_view_settings', view_settings)
                return view_settings
        raise Http404

    def check_predicates(self, view_settings, request, req_args, req_kw):
        predicates = view_settings['predicates']

        # here predicate is an instance object
        for predicate in predicates:
            is_passed = predicate(None, request)
            if not is_passed:
                return is_passed, request

        return True, request

    def process_callback_response(self, request, response, view_settings):
        if isinstance(response, Response):
            # Do not process standard django responses
            return response
        renderer = view_settings['renderer']
        return renderer(request, response)
