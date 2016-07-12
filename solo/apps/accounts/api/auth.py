from typing import Dict, Any

from aiohttp import web
from aiohttp.web import HTTPFound
from aiohttp_session import get_session

from solo import http_defaults, http_endpoint
from solo.apps.accounts.service import AuthService


@http_defaults(route_name='/login/{provider}', renderer='json')
class BackendAuthenticationHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='POST')
    async def init_authentication(self) -> web.Response:
        provider = self.request.app['solo.apps.accounts'][self.context['provider'].value]
        url = await provider.authorize(self.request)
        return HTTPFound(location=url)


@http_defaults(route_name='/login/{provider}/callback', renderer='json')
class BackendAuthenticationCallbackHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='GET')
    async def process_callback(self) -> web.Response:
        """

        """
        request = self.request
        app = request.app
        provider = app['solo.apps.accounts'][self.context['provider'].value]
        auth_service = AuthService(app)

        integration = await provider.callback(request)
        user = await auth_service.user_from_integration(integration)
        session = await get_session(request)
        _ok_ = auth_service.user_to_session(user, session)
        return HTTPFound(location='/authenticated')


