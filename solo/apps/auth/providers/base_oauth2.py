from typing import List, Optional, Tuple
from urllib.parse import urlencode
import uuid

from aiohttp_session import get_session
from aiohttp import web

from ..models import AuthProvider
from ..exceptions import CSRFError, AuthorizationError


class ThirdPartyProfile:
    def __init__(self, id: str, display_name: str, email: Optional[str] = None):
        self.id = id
        self.display_name = display_name
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
        """ Field name to consult when a provider returns an error response.
        """

    async def authorize(self, request: web.Request) -> str:
        """ Init internal authorization state and return necessary data for performing authorization.

        :return: URL to redirect to in order to initialize authorization with a 3rd-party service
        """
        session = await get_session(request)
        session['oauth.state'] = state = uuid.uuid4().hex
        url = self.get_authorization_payload(state=state)
        return url

    async def callback(self, request: web.Request) -> ProfileIntegration:
        raise NotImplementedError("Implement me")

    async def validate_callback(self, request: web.Request) -> Tuple[str, str]:
        """
        :return: 2-tuple of (session state, OAuth2 exchangeable code)
        """
        session = await get_session(request)
        session_state = session.pop('oauth.state', None)
        request_state = request.GET.get('state')
        if not session_state or session_state != request_state:
            raise CSRFError(
                    'State mismatch. Requested: {request_state}. Actual: {session_state}'.format(
                            request_state=request_state,
                            session_state=session_state
                    )
            )
        code = request.GET.get('code')
        if not code:
            reason = request.GET.get('error', 'n/a')
            error_description = request.GET.get('error_description', '(no description)')
            raise AuthorizationError("Authorization code was not provided. Reason: {} {}".format(reason, error_description),
                                     reason=reason, provider=self)
        return (session_state, code)

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
