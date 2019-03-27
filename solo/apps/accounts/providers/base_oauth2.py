import uuid
from typing import Optional, Tuple, Sequence
from urllib.parse import urlencode

from solo.vendor.old_session.old_session import Session

from solo.apps.accounts.exceptions import CSRFError, AuthorizationError
from solo.apps.accounts.model import AuthProvider
from solo.server.request import Request


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
    def __init__(self,
        client_id: str,
        client_secret: str,
        scope: Sequence[str],
        redirect_uri: str,
        authorize_url: str,
        access_token_url: str,
        profile_url: str
    ):
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

    async def authorize(self, session: Session) -> str:
        """ Init internal authorization state and return necessary data for performing authorization.

        :return: URL to redirect to in order to initialize authorization with a 3rd-party service
        """
        session['oauth.state'] = state = uuid.uuid4().hex
        url = self.get_authorization_payload(state=state)
        return url

    async def callback(self, request: Request, session: Session) -> ProfileIntegration:
        raise NotImplementedError("Implement me")

    async def validate_callback_exn(self,
        request: Request,
        session: Session
    ) -> Tuple[str, str]:
        """
        :return: 2-tuple of (session state, OAuth2 exchangeable code)
        """
        session_state = session.pop('oauth.state', None)
        request_state = request.qs_params.get('state')
        if not session_state or session_state != request_state:
            raise CSRFError(
                f'State mismatch. '
                f'Requested: {request_state}. '
                f'Actual: {session_state}'
            )
        code = request.qs_params.get('code')
        if not code:
            reason = request.qs_params.get('error', 'n/a')
            error_description = request.qs_params.get('error_description', '(no description)')
            raise AuthorizationError(
                f"Authorization code was not provided. Reason: {reason} {error_description}",
                reason=reason, provider=self
            )
        return (session_state, code)

    def get_authorization_payload(self, state: str) -> str:
        url_params = urlencode(dict(
            scope=self.scope_str,
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            state=state
        ))
        return f'{self.authorize_url}?{url_params}'

    def get_access_token_payload(self, state: str, code: str) -> str:
        url_params = urlencode(dict(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            code=code,
            state=state
        ))
        return f'{self.access_token_url}?{url_params}'

    def get_profile_payload(self, access_token: str) -> str:
        url_params = urlencode(dict(
            access_token=access_token
        ))
        return f'{self.profile_url}?{url_params}'
