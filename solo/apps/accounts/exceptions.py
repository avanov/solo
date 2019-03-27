from solo.server.statuses import Http4xx


class CSRFError(Http4xx):
    status = 403


class AuthorizationError(Exception):
    def __init__(self, msg, reason, provider):
        super(AuthorizationError, self).__init__(msg)
        self.reason = reason
        self.provider = provider


class ProviderServiceError(Exception):
    pass
