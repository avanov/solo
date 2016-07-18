from aiohttp.web import Request

from solo.apps.accounts.model import UserType
from solo.apps.accounts.service import AuthService
from solo.apps.accounts.service import USER_KEY
from .model import Guest


async def get_user(request: Request) -> UserType:
    try:
        user = request[USER_KEY]
    except KeyError:
        auth_service = AuthService(request.app)
        user = await auth_service.session_user(request)
        user = user or Guest
        request[USER_KEY] = user
    return user


async def allowed(user: UserType, permission: str) -> bool:
    permissions = await user.permissions()