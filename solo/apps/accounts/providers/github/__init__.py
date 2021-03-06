import json
import logging
from typing import List, Optional

from httpx import AsyncClient

from solo.apps.accounts.exceptions import ProviderServiceError
from solo.apps.accounts.model import AuthProvider
from solo.apps.accounts.providers.base_oauth2 import OAuth2Provider, ThirdPartyProfile, ProfileIntegration
from solo.server.request import Request
from solo.vendor.old_session.old_session import Session

from .definitions import AuthenticatedUser, MakeAuthenticatedUser


log = logging.getLogger(__name__)


@AuthProvider.GITHUB.bind(AuthProvider.Contract.auth_provider_impl)
class GithubProvider(OAuth2Provider):
    """ Github OAuth2 provider.

    * Application management: https://github.com/settings/developers
    * API reference: https://developer.github.com/v3/oauth/

    """
    def __init__(self, client_id: str, client_secret: str, scope: List[str], redirect_uri: Optional[str] = None):
        """
        :param redirect_uri: The redirect_uri parameter is optional. If left out, GitHub will redirect users to the
                             callback URL configured in the OAuth Application settings.
        """
        super().__init__(client_id, client_secret, scope,
                         redirect_uri=redirect_uri,
                         authorize_url='https://github.com/login/oauth/authorize',
                         access_token_url='https://github.com/login/oauth/access_token',
                         profile_url='https://api.github.com/user')

    async def callback(self, request: Request, session: Session) -> ProfileIntegration:
        """ Process github redirect
        """
        session_state, code = await self.validate_callback_exn(request, session)

        # Now retrieve the access token with the code
        access_url = self.get_access_token_payload(session_state, code)
        headers = {'Accept': 'application/json'}
        with AsyncClient() as http:
            async with http.get(access_url, headers=headers) as r:
                if r.status_code != 200:
                    content = r.text
                    raise ProviderServiceError(
                        f'Service responded with status {r.status}: {content}'
                    )
                else:
                    content = json.loads(r.text)
                access_token = content['access_token']

                # Retrieve profile data
                profile_url = self.get_profile_payload(access_token=access_token)
                async with http.get(profile_url, headers=headers) as profile_r:
                    if profile_r.status_code != 200:
                        content = profile_r.text
                        raise ProviderServiceError(
                            f"Error during profile retrieval. Status {profile_r.status}: {content}"
                        )
                    else:
                        profile_data = json.loads(profile_r.text)
                        profile_data: AuthenticatedUser = MakeAuthenticatedUser(profile_data)

                    profile = ThirdPartyProfile(
                        id=str(profile_data.id),
                        display_name=profile_data.name or profile_data.login,
                        # email might be non-verified
                        email=profile_data.email
                    )

                    return ProfileIntegration(provider=AuthProvider.GITHUB,
                                              access_token=access_token,
                                              profile=profile)
