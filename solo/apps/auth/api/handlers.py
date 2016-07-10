from typing import Dict, Any

from aiohttp import web
from aiohttp.web import HTTPFound, HTTPForbidden
from aiohttp_session import get_session

from solo import http_defaults, http_endpoint
from solo.server import responses
from ..service import AuthService


@http_defaults(route_name='/login/be/{provider}', renderer='json')
class BackendAuthenticationHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='POST')
    async def init_authentication(self) -> web.Response:
        provider = self.request.app['solo.apps.auth'][self.context['provider'].value]
        url = await provider.authorize(self.request)
        return HTTPFound(location=url)


@http_defaults(route_name='/login/be/{provider}/callback', renderer='json')
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
        provider = app['solo.apps.auth'][self.context['provider'].value]
        auth_service = AuthService(app)

        integration = await provider.callback(request)
        user = await auth_service.user_from_integration(integration)
        session = await get_session(request)

        _ok_ = auth_service.user_to_session(user, session)
        return HTTPFound(location='/authenticated')


@http_defaults(route_name='/login/fe', renderer='json')
class FrontendAuthenticationHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='POST')
    async def authenticate_frontend(self):
        """
        """
        request = self.request
        app = request.app
        auth_service = AuthService(app)
        session = await get_session(request)
        user = await auth_service.user_from_session(session)
        if user is None:
            return HTTPForbidden()
        return {
            'id': str(user.id),
            'type': 'users',
            'attributes': user.as_dict(),
        }
