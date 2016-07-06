from aiohttp import web
from typing import Dict, Any

from solo import http_defaults, http_endpoint
from solo.server import responses
from ..service import AuthService


@http_defaults(route_name='/login/{provider}', renderer='json')
class AuthenticationHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='GET')
    async def init_authorization(self) -> web.Response:
        provider = self.request.app['solo.apps.auth'][self.context['provider'].value]
        url = await provider.authorize(self.request)
        return {'location': url}


@http_defaults(route_name='/login/{provider}/callback', renderer='json')
class AuthenticationCallbackHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='GET')
    async def process_callback(self) -> web.Response:
        """

        """
        app = self.request.app
        provider = app['solo.apps.auth'][self.context['provider'].value]
        integration = await provider.callback(self.request)
        auth_service = AuthService(app)
        user = await auth_service.user_from_integration(integration)
        return user.as_dict()
