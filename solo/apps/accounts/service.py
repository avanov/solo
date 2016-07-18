import logging
from typing import Optional, Set, Dict

from aiohttp.web import Application
from aiohttp.web import Request
from aiohttp_session import get_session
from sqlalchemy import select

from solo.apps.accounts.model import Auth, User, UserType, Guest, Group, users_groups_association, Permissions
from solo.apps.accounts.providers.base_oauth2 import ProfileIntegration

from solo.services import SQLService


log = logging.getLogger(__name__)

USER_KEY = '__user__'


class UserService(SQLService):
    def __init__(self, app: Application):
        super(UserService, self).__init__(app, User)
        self._permissions = {}  # type: Dict[int, Permissions]

    async def permissions(self, user: UserType) -> Permissions:
        if user is Guest:
            return Permissions(Guest, set())
        try:
            permissions = self._permissions[user.id]
        except KeyError:
            query = (select(self.columns([Group.permissions], entity=Group))
                    .select_from(users_groups_association.join(
                        Group,
                        users_groups_association.c.group_id == Group.id
                    ))
                    .where(users_groups_association.c.user_id == user.id))

            async with self.engine.acquire() as c:
                csr = await c.execute(query)
                groups = await csr.fetchall()
                permissions = set()
                map(lambda x: permissions.add(x['permissions']), groups)

            permissions = Permissions(user, permissions)
            self._permissions[user.id] = permissions

        return permissions


class AuthService(SQLService):

    def __init__(self, app: Application):
        super(AuthService, self).__init__(app, Auth)
        self.user_service = UserService(app)

    async def user_to_session(self, request: Request, user: User) -> bool:
        session = await get_session(request)
        session[USER_KEY] = user.id
        return True

    async def session_user(self, request: Request) -> Optional[User]:
        session = await get_session(request)
        try:
            user_id = session[USER_KEY]
        except KeyError:
            return None
        user = await self.user_service.get(User.id, user_id)
        return user

    async def user_from_integration(self, integration: ProfileIntegration) -> User:
        """ Returns either an existing user associated with a given 3rd-party integration, or a newly created one.

        :param integration: integration credentials retrieved after successful OAuth authentication.
        :return: User entity
        """
        query = (select(self.columns(entity=User))
                .select_from(Auth.__table__.join(
                    User,
                    Auth.user_id == User.id
                ))
                .where(Auth.provider == integration.provider)
                .where(Auth.provider_uid == integration.profile.id))

        async with self.engine.acquire() as c:
            csr = await c.execute(query)
            user = await csr.fetchone()
            if user is None:
                log.debug('Creating a new user account from {provider} integration'.format(provider=integration.provider.value))
                user = User(name=integration.profile.display_name)
                user = await self.user_service.save(user)
                # Insert auth entry
                auth = Auth(provider=integration.provider,
                            provider_uid=integration.profile.id,
                            access_token=integration.access_token,
                            user_id=user.id)
                await self.save(auth)
            else:
                user = User(**dict(user))
                # Update access token
                query = (self.t.update()
                        .values(access_token=integration.access_token)
                        .where(Auth.provider == integration.provider)
                        .where(Auth.provider_uid == integration.profile.id))
                _csr_ = await c.execute(query)

            return user
