from typing import Dict, Any

from solo import http_defaults, http_endpoint
from solo.apps.accounts.service import AuthService
from solo.configurator.registry import Registry
from solo.server.request import Request
from solo.server.db.types import SQLEngine
from solo.server.definitions import HttpMethod
from solo.server.statuses import Redirect
from solo.vendor.old_session.old_session import Session


@http_defaults(route_name='/login/{provider}', renderer='json')
class BackendAuthenticationHandler:

    def __init__(self, request: Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method=HttpMethod.POST)
    async def init_authentication(
        self,
        reg: Registry,
        sess: Session
    ) -> None:
        provider = reg.settings['solo.apps.accounts'][self.context['provider'].value]

        url = await provider.authorize(sess)
        raise Redirect(location=url)


@http_defaults(route_name='/login/{provider}/callback', renderer='json')
class BackendAuthenticationCallbackHandler:

    def __init__(self, request: Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method=HttpMethod.GET)
    async def process_callback(
        self,
        reg: Registry,
        db: SQLEngine,
        sess: Session,
    ) -> None:
        """
        """
        request = self.request
        provider = reg.settings['solo.apps.accounts'][self.context['provider'].value]
        auth_service = AuthService(db)

        integration = await provider.callback(request, sess)
        user = await auth_service.user_from_integration(integration)
        _ok_ = await auth_service.user_to_session(request, user)
        raise Redirect(location='/authenticated')
