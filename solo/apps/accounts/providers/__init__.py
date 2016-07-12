import logging
from typing import List
from solo import Configurator
from solo.apps.accounts.models import AuthProvider

log = logging.getLogger(__name__)


def enable_provider(config: Configurator,
                    name: str,
                    client_id: str,
                    client_secret: str,
                    scope: List[str]):
    log.debug('Enabling authentication provider: {}'.format(name.upper()))
    provider = AuthProvider.match(name)
    auth_registry = config.registry.setdefault('solo.apps.accounts', {})
    redirect_uri = '{}{}'.format(
        config.registry['config']['server']['public_uri'].rstrip('/'),
        config.router.url('solo.apps.accounts:/login/{provider}/callback', parts={'provider': provider.value})
    )
    provider_impl = provider['auth_provider_impl']
    auth_registry[name] = provider_impl(client_id=client_id,
                                        client_secret=client_secret,
                                        scope=scope,
                                        redirect_uri=redirect_uri)
