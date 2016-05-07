from aiohttp import web
from typing import Dict, Any

from solo import http_defaults, http_endpoint


@http_defaults(route_name='/login/{provider}')
class AuthenticationHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='GET')
    async def init_authorization(self) -> web.Response:
        provider = self.context['provider']['auth_provider_impl']()
        return (await provider.authorize())


@http_defaults(route_name='/login/{provider}/callback')
class AuthenticationCallbackHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='GET')
    async def process_callback(self) -> web.Response:
        provider = self.context['provider']['auth_provider_impl']()
        integration = await provider.callback()
        return {}
