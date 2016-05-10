from aiohttp import web
from typing import Dict, Any

from solo import http_defaults, http_endpoint


@http_defaults(route_name='/login/{provider}', renderer='json')
class AuthenticationHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='GET')
    async def init_authorization(self) -> web.Response:
        provider = self.request.app['solo.apps.auth'][self.context['provider'].value]
        url = await provider.authorize(self.request)
        return web.HTTPFound(location=url)


@http_defaults(route_name='/login/{provider}/callback')
class AuthenticationCallbackHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='GET')
    async def process_callback(self) -> web.Response:
        provider = self.request.app['solo.apps.auth'][self.context['provider'].value]
        integration = await provider.callback(self.request)
        return {
            'id': integration.profile.id,
            'username': integration.profile.username,
            'email': integration.profile.email
        }
