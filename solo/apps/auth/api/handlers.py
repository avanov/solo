from aiohttp import web

from solo import http_defaults, http_endpoint


@http_defaults(route_name='/login/{provider}')
class AuthenticationHandler:

    def __init__(self, request: web.Request):
        self.request = request

    @http_endpoint(request_method='GET')
    async def get(self):
        return {}
