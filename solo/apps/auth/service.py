import logging
from typing import Optional

from aiohttp.web import Application
from aiohttp_session import Session
from sqlalchemy.sql import select

from solo.services import SQLService
from solo.apps.accounts.models import User
from solo.apps.accounts.service import UserService

from .providers.base_oauth2 import ProfileIntegration
from .models import Auth


log = logging.getLogger(__name__)


class AuthService(SQLService):
    SESSION_USER_KEY = 'user_id'

    def __init__(self, app: Application):
        super(AuthService, self).__init__(app, Auth)
        self.user_service = UserService(app)

    def user_to_session(self, user: User, session: Session) -> bool:
        session[self.SESSION_USER_KEY] = user.id
        return True

    async def user_from_session(self, session: Session) -> Optional[User]:
        try:
            user_id = session[self.SESSION_USER_KEY]
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

