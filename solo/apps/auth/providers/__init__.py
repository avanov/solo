import logging
from pathlib import Path
from typing import List
from solo import Configurator
from ..models import AuthProvider


log = logging.getLogger(__name__)


def enable_provider(config: Configurator,
                    name: str,
                    client_id: str,
                    client_secret: str,
                    scope: List[str]):
    log.debug('Enabling authentication provider: {}'.format(name.upper()))
    provider = AuthProvider.match(name)['auth_provider_impl']
    auth_registry = config.registry.setdefault('solo.apps.auth', {})
    redirect_uri = Path(config.router.route_prefix, 'login', name, 'callback')
    auth_registry[name] = provider(client_id=client_id,
                                   client_secret=client_secret,
                                   scope=scope,
                                   redirect_uri=redirect_uri)
