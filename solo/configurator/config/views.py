import inspect

from . import predicates as default_predicates
from ..util import viewdefaults
from .routes import ViewMeta
from .util import PredicateList


class ViewsConfigurator:

    def __init__(self):
        self.predicates = PredicateList()

    @viewdefaults
    def add_view(self,
                 view=None,
                 route_name=None,
                 request_method=None,
                 attr=None,
                 decorator=None,
                 renderer=None,
                 **predicates) -> ViewMeta:
        """

        :param view: callable
        :param route_name:
        :type route_name: str or None
        :param request_method:
        :type request_method: str or tuple
        :param attr:
          This knob is most useful when the view definition is a class.

          The view machinery defaults to using the ``__call__`` method
          of the :term:`view callable` (or the function itself, if the
          view callable is a function) to obtain a response.  The
          ``attr`` value allows you to vary the method attribute used
          to obtain the response.  For example, if your view was a
          class, and the class has a method named ``index`` and you
          wanted to use this method instead of the class' ``__call__``
          method to return the response, you'd say ``attr="index"`` in the
          view configuration for the view.
        :type attr: str
        :param decorator:
        :param renderer:
        :param predicates: Pass a key/value pair here to use a third-party predicate
                           registered via
                           :meth:`solo.configurator.config.Configurator.views.add_view_predicate`.
                           More than one key/value pair can be used at the same time. See
                           :ref:`view_and_route_predicates` for more information about
                           third-party predicates.
        :return: :raise ConfigurationError:
        """
        # Parse view
        # -----------------------------------------------
        if inspect.isclass(view) and attr is None:
            attr = '__call__'

        # Add decorators
        # -----------------------------------------------
        def combine(*decorators):
            def decorated(view_callable):
                # reversed() is allows a more natural ordering in the api
                for decorator in reversed(decorators):
                    view_callable = decorator(view_callable)
                return view_callable
            return decorated

        if isinstance(decorator, tuple):
            decorator = combine(*decorator)

        if decorator:
            view = decorator(view)

        # Register predicates
        # -------------------------------------
        if request_method is None:
            request_method = ('GET',)
        pvals = predicates.copy()
        pvals.update(
            dict(
                request_method=request_method,
                )
            )
        predlist = self.get_predlist('view')
        _weight_, preds, _phash_ = predlist.make(self, **pvals)

        # Renderers
        # -------------------------------------
        if renderer is None:
            renderer = 'string'

        # Done
        # -------------------------------------
        view_item = ViewMeta(route_name=route_name,
                             view=view,
                             attr=attr,
                             renderer=renderer,
                             predicates=preds)
        return view_item

    def get_predlist(self, name):
        """ This is a stub method that simply has the same signature as pyramid's version,
        but does nothing but returning ``self.predicates``
        """
        return self.predicates

    def add_view_predicate(self, name, factory, weighs_more_than=None,
                           weighs_less_than=None):
        """
        Adds a view predicate factory.  The associated view predicate can
        later be named as a keyword argument to
        :meth:`solo.configurator.config.Configurator.views.add_view` in the
        ``predicates`` anonymous keyword argument dictionary.

        ``name`` should be the name of the predicate.  It must be a valid
        Python identifier (it will be used as a keyword argument to
        ``add_view`` by others).

        ``factory`` should be a :term:`predicate factory` or :term:`dotted
        Python name` which refers to a predicate factory.

        See :ref:`view_and_route_predicates` for more information.
        """
        self._add_predicate(
            'view',
            name,
            factory,
            weighs_more_than=weighs_more_than,
            weighs_less_than=weighs_less_than
            )

    def add_default_view_predicates(self):
        p = default_predicates
        for name, factory in (
            ('request_method', p.RequestMethodPredicate),
            ):
            self.add_view_predicate(name, factory)


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