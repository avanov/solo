from typing import Dict, Any

from aiohttp import web
from aiohttp.web import HTTPFound, HTTPForbidden

from solo import http_defaults, http_endpoint
from solo.apps.accounts.service import UserService
from solo.apps.accounts.models import User, Guest
from solo.apps.accounts import get_user


@http_defaults(route_name='/users')
class AccountsListHandler:

    def __init__(self, request: web.Request):
        self.request = request

    @http_endpoint(request_method='GET')
    async def get(self):
        return {}


@http_defaults(route_name='/users/me', renderer='json')
class FrontendAuthenticationHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method='GET')
    async def authenticate_frontend(self):
        """
        """
        user = await get_user(self.request)
        if user is Guest:
            return HTTPForbidden()
        return {
            'id': str(user.id),
            'type': 'users',
            'attributes': user.as_dict(),
        }


@http_defaults(route_name='/users/{userId}', renderer='json')
class AccountDetailsHandler:

    def __init__(self, request: web.Request, context: Dict[str, Any]):
        self.request = request
        self.context = context
        print(context)

    @http_endpoint(request_method='GET')
    async def get(self):

        user_service = UserService(self.request.app)
        user = await user_service.get(User.id, self.context['userId'])
        if not user:
            return HTTPForbidden()
        return {
            'id': str(user.id),
            'type': 'users',
            'attributes': user.as_dict(),
        }
