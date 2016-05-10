from typing import List, Optional
from urllib.parse import urlencode

from aiohttp import web

from ..models import AuthProvider


class ThirdPartyProfile:
    def __init__(self, id: str, username: str, email: Optional[str] = None):
        self.id = id
        self.username = username
        self.email = email


class ProfileIntegration:
    __slots__ = ('provider', 'profile', 'access_token')
    def __init__(self,
                 provider: AuthProvider,
                 access_token: str,
                 profile: ThirdPartyProfile):
        self.provider = provider
        self.profile = profile
        self.access_token = access_token


class OAuth2Provider:
    def __init__(self, client_id: str,
                 client_secret: str,
                 scope: List[str],
                 redirect_uri: str,
                 authorize_url: str,
                 access_token_url: str,
                 profile_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.scope_str = ','.join(scope)
        self.redirect_uri = redirect_uri
        self.authorize_url = authorize_url
        self.access_token_url = access_token_url
        self.profile_url = profile_url

    async def authorize(self, request: web.Request) -> web.Response:
        raise NotImplementedError("Implement me")

    async def callback(self, request: web.Request) -> ProfileIntegration:
        raise NotImplementedError("Implement me")

    def get_authorization_payload(self, state):
        return '{}?{}'.format(self.authorize_url, urlencode(dict(
            scope=self.scope_str,
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            state=state
        )))

    def get_access_token_payload(self, state: str, code: str) -> str:
        return '{}?{}'.format(self.access_token_url, urlencode(dict(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            code=code,
            state=state
        )))

    def get_profile_payload(self, access_token: str) -> str:
        return '{}?{}'.format(self.profile_url, urlencode(dict(
            access_token=access_token
        )))
