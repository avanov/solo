import logging
from aiohttp.web import Application
from sqlalchemy.sql import select

from solo.services import SQLService
from solo.apps.accounts.models import User
from solo.apps.accounts.service import UserService

from .providers.base_oauth2 import ProfileIntegration
from .models import Auth


log = logging.getLogger(__name__)


class AuthService(SQLService):
    def __init__(self, app: Application):
        super(AuthService, self).__init__(app, Auth)

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
                user_service = UserService(self.app)
                user = User(name=integration.profile.username)
                user = await user_service.save(user)
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

