import json
import logging
from typing import List, Optional

from httpx import AsyncClient

from solo.server.request import Request
from solo.apps.accounts.model import AuthProvider
from solo.apps.accounts.exceptions import ProviderServiceError
from .base_oauth2 import OAuth2Provider, ThirdPartyProfile, ProfileIntegration


log = logging.getLogger(__name__)


@AuthProvider.FACEBOOK.bind(AuthProvider.Contract.auth_provider_impl)
class FacebookProvider(OAuth2Provider):
    """ Facebook OAuth2 provider.

    * Application management: https://developers.facebook.com/apps/
    * API reference: https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow

    """
    def __init__(self, client_id: str, client_secret: str, scope: List[str], redirect_uri: Optional[str] = None):
        """
        :param redirect_uri: The redirect_uri parameter is optional. If left out, GitHub will redirect users to the
                             callback URL configured in the OAuth Application settings.
        """
        super(FacebookProvider, self).__init__(client_id, client_secret, scope,
                                               redirect_uri=redirect_uri,
                                               authorize_url='https://www.facebook.com/dialog/oauth',
                                               access_token_url='https://graph.facebook.com/v2.6/oauth/access_token',
                                               profile_url='https://graph.facebook.com/v2.6/me')


    async def callback(self, request: Request) -> ProfileIntegration:
        """ Process github redirect
        """
        session_state, code = await self.validate_callback_exn(request)

        # Now retrieve the access token with the code
        access_url = self.get_access_token_payload(session_state, code)
        headers = {'Accept': 'application/json'}
        with AsyncClient() as http:
            async with http.get(access_url, headers=headers) as r:
                if r.status_code != 200:
                    content = r.text
                    raise ProviderServiceError(
                        f'Service responded with status {r.status_code}: {content}'
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
                            f'Error during profile retrieval. Status {profile_r.status}: {content}'
                        )
                    else:
                        profile_data = json.loads(profile_r.text)

                    profile = ThirdPartyProfile(id=str(profile_data['id']),
                                                display_name=profile_data['name'],
                                                # email might be non-verified
                                                email=profile_data.get('email'))

                    return ProfileIntegration(provider=AuthProvider.FACEBOOK,
                                              access_token=access_token,
                                              profile=profile)
