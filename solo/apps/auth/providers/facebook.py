import logging
from typing import List, Optional

from aiohttp import web
from aiohttp import ClientSession

from ..models import AuthProvider
from .base_oauth2 import OAuth2Provider, ThirdPartyProfile, ProfileIntegration
from ..exceptions import ProviderServiceError


log = logging.getLogger(__name__)


@AuthProvider.FACEBOOK(category='auth_provider_impl')
class FacebookProvider(OAuth2Provider):
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


    async def callback(self, request: web.Request) -> ProfileIntegration:
        """ Process github redirect
        """
        session_state, code = await self.validate_callback(request)

        # Now retrieve the access token with the code
        access_url = self.get_access_token_payload(session_state, code)
        with ClientSession(headers={'Accept': 'application/json'}) as http:
            async with http.get(access_url) as r:
                if r.status != 200:
                    content = await r.text()
                    raise ProviderServiceError('Service responded with status {}: {}'.format(r.status, content))
                else:
                    content = await r.json()
                access_token = content['access_token']

                # Retrieve profile data
                profile_url = self.get_profile_payload(access_token=access_token)
                async with http.get(profile_url) as profile_r:
                    if profile_r.status != 200:
                        content = await profile_r.text()
                        raise ProviderServiceError("Error during profile retrieval. Status {}: {}".format(
                            profile_r.status,
                            content
                        ))
                    else:
                        profile_data = await profile_r.json()

                    profile = ThirdPartyProfile(id=str(profile_data['id']),
                                                display_name=profile_data['name'],
                                                # email might be non-verified
                                                email=profile_data.get('email'))

                    return ProfileIntegration(provider=AuthProvider.FACEBOOK,
                                              access_token=access_token,
                                              profile=profile)
