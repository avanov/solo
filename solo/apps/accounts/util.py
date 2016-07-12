from typing import TypeVar
from aiohttp_session import get_session
from aiohttp.web import Request

from solo.apps.accounts.service import USER_KEY
from solo.apps.accounts.service import UserService
from .models import User, Guest


UserType = TypeVar('UserType', User, Guest)


async def get_user(request: Request) -> UserType:
    try:
        user = request[USER_KEY]
    except KeyError:
        session = await get_session(request)
        try:
            user_id = session[USER_KEY]
        except KeyError:
            user = Guest
        else:
            user_service = UserService(request.app)
            user = await user_service.get(User.id, user_id)
            user = user or Guest
        request[USER_KEY] = user
    return user
