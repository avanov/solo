from solo import Configurator
from .util import get_user

from solo.apps.accounts.providers import enable_provider
from . import predicate


__all__  = ['get_user']


def includeme(config: Configurator):
    config.include_api_specs(__name__, 'api/specs.raml')
    config.add_directive(enable_provider)
    config.views.add_view_predicate('permission', predicate.PermissionPredicate,
                                    weighs_more_than='request_method')
    config.views.add_view_predicate('authenticated', predicate.AuthenticatedPredicate,
                                    weighs_less_than='permission')

