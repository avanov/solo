import logging
from typing import Optional

from solo.server.statuses import Http4xx
from solo.server.request import Request
from solo.server.runtime.dependencies import Runtime
from .util import get_user
from .service import UserService
from .model import Guest


log = logging.getLogger(__name__)


class PermissionPredicate:
    def __init__(self, val, config, raises: Optional[Http4xx] = None):
        log.debug(f'Registered permission predicate: {val}')
        config.available_permissions.add(val)
        self.val = val
        self.raises = raises

    def text(self) -> str:
        return f'permission = {self.val}'

    phash = text

    async def __call__(self, runtime: Runtime, request: Request) -> bool:
        user_service = UserService(runtime.dbengine)
        user = await get_user(
            runtime.session_storage,
            runtime.dbengine,
            request
        )
        permissions = await user_service.permissions(user)
        return permissions.allowed(self.val)


class AuthenticatedPredicate:
    def __init__(self, val: bool, config, raises: Optional[Http4xx] = None):
        self.val = val
        self.raises = raises

    def text(self):
        return 'authenticated = {}'.format(self.val)

    phash = text

    async def __call__(self, context, request: Request) -> bool:
        user = await get_user(request)
        if self.val:
            return user is not Guest
        return user is Guest
