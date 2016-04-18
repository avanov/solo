from solo import http_defaults, http_endpoint
from aiohttp import web


@http_defaults(route_name='/')
class AccountsListHandler:

    def __init__(self, request: web.Request):
        self.request = request

    @http_endpoint(request_method='GET')
    def get(self):
        return {}


@http_defaults(route_name='/{userId}')
class AccountDetailsHandler:

    def __init__(self, request: web.Request):
        self.request = request

    @http_endpoint(request_method='GET')
    def get(self):
        return {}