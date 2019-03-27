from solo.server.db.types import SQLEngine
from solo.server.request import Request
from solo.apps.accounts.model import UserType
from solo.apps.accounts.service import AuthService
from solo.apps.accounts.service import USER_KEY
from solo.vendor.old_session.old_session import SessionStore
from .model import Guest


async def get_user(store: SessionStore, db: SQLEngine, request: Request) -> UserType:
    try:
        user = request[USER_KEY]
    except KeyError:
        auth_service = AuthService(db)
        user = await auth_service.session_user(request)
        user = user or Guest
        request[USER_KEY] = user
    return user


async def allowed(user: UserType, permission: str) -> bool:
    permissions = await user.permissions()