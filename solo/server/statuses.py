class HttpStatus(Exception):
    pass


class Http4xx(HttpStatus):
    status: int = 400


class NotFound(Http4xx):
    status = 404


class Forbidden(Http4xx):
    status = 403


class Http3xx(HttpStatus):
    status: int = 302


class Redirect(Http3xx):
    def __init__(self, location: str):
        self.location = location
