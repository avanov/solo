from typing import Dict, Any

from solo import http_defaults, http_endpoint
from solo.apps.accounts.service import UserService
from solo.apps.accounts.model import User, Guest
from solo.apps.accounts import get_user
from solo.server.db import SQLEngine
from solo.server.request import Request
from solo.server.definitions import HttpMethod
from solo.server.statuses import Forbidden
from solo.vendor.old_session.old_session import SessionStore


@http_defaults(route_name='/users', permission='users:view', renderer='json')
class AccountsListHandler:

    def __init__(self, request: Request, context: Dict[str, Any]):
        self.request = request

    @http_endpoint(request_method=HttpMethod.GET)
    async def get(self):
        return {}


@http_defaults(route_name='/users/me', authenticated=True, renderer='json')
class FrontendAuthenticationHandler:

    def __init__(self, request: Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method=HttpMethod.GET)
    async def authenticate_frontend(self,
                                    store: SessionStore,
                                    db: SQLEngine):
        """
        """
        user = await get_user(store, db, self.request)
        if user is Guest:
            raise Forbidden()
        return {
            'id': str(user.id),
            'type': 'users',
            'attributes': user.as_dict(),
        }


@http_defaults(route_name='/users/{userId}', authenticated=True, renderer='json')
class AccountDetailsHandler:

    def __init__(self, request: Request, context: Dict[str, Any]):
        self.request = request
        self.context = context

    @http_endpoint(request_method=HttpMethod.GET)
    async def get(self):

        user_service = UserService(self.request.app)
        user = await user_service.get(User.id, self.context['userId'])
        if not user:
            raise Forbidden()
        return {
            'id': str(user.id),
            'type': 'users',
            'attributes': user.as_dict(),
        }
