import uuid

from aiohttp_session import get_session


class SessionCSRFStoragePolicy:
    """ Taken from
    https://github.com/Pylons/pyramid/blob/3ee04cc62205b10eb9041b0df5e156936765202f/pyramid/csrf.py#L57

    A CSRF storage policy that persists the CSRF token in the session.

    Note that using this CSRF implementation requires that
    a :term:`session factory` is configured.

    ``key``

        The session key where the CSRF token will be stored.
        Default: `_csrft_`.

    """
    _token_factory = staticmethod(lambda: uuid.uuid4().hex)

    def __init__(self, key: str = '_csrft_') -> None:
        self.key = key

    async def new_csrf_token(self, request):
        """ Sets a new CSRF token into the session and returns it. """
        session = await get_session(request)
        token = self._token_factory()
        session[self.key] = token
        return token

    async def get_csrf_token(self, request):
        """ Returns the currently active CSRF token from the session,
        generating a new one if needed."""
        session = await get_session(request)
        token = session.get(self.key, None)
        if not token:
            token = await self.new_csrf_token(request)
        return token

    async def check_csrf_token(self, request, supplied_token):
        """ Returns ``True`` if the ``supplied_token`` is valid."""
        expected_token = await self.get_csrf_token(request)
        return expected_token == supplied_token


def get_csrf_token(request):
    """ Taken from
    https://github.com/Pylons/pyramid/blob/3ee04cc62205b10eb9041b0df5e156936765202f/pyramid/csrf.py#L159

    Get the currently active CSRF token for the request passed, generating
    a new one using ``new_csrf_token(request)`` if one does not exist. This
    calls the equivalent method in the chosen CSRF protection implementation.

    .. versionadded :: 1.9

    """
    registry = request.registry
    csrf = registry.getUtility(ICSRFStoragePolicy)
    return csrf.get_csrf_token(request)


def new_csrf_token(request):
    """ Taken from
    https://github.com/Pylons/pyramid/blob/3ee04cc62205b10eb9041b0df5e156936765202f/pyramid/csrf.py#L172

    Generate a new CSRF token for the request passed and persist it in an
    implementation defined manner. This calls the equivalent method in the
    chosen CSRF protection implementation.

    .. versionadded :: 1.9

    """
    registry = request.registry
    csrf = registry.getUtility(ICSRFStoragePolicy)
    return csrf.new_csrf_token(request)


def check_csrf_token(request,
                     token='csrf_token',
                     header='X-CSRF-Token',
                     raises=True):
    """ Taken from
    https://github.com/Pylons/pyramid/blob/3ee04cc62205b10eb9041b0df5e156936765202f/pyramid/csrf.py#L185

    Check the CSRF token returned by the
    :class:`pyramid.interfaces.ICSRFStoragePolicy` implementation against the
    value in ``request.POST.get(token)`` (if a POST request) or
    ``request.headers.get(header)``. If a ``token`` keyword is not supplied to
    this function, the string ``csrf_token`` will be used to look up the token
    in ``request.POST``. If a ``header`` keyword is not supplied to this
    function, the string ``X-CSRF-Token`` will be used to look up the token in
    ``request.headers``.

    If the value supplied by post or by header cannot be verified by the
    :class:`pyramid.interfaces.ICSRFStoragePolicy`, and ``raises`` is
    ``True``, this function will raise an
    :exc:`pyramid.exceptions.BadCSRFToken` exception. If the values differ
    and ``raises`` is ``False``, this function will return ``False``.  If the
    CSRF check is successful, this function will return ``True``
    unconditionally.

    See :ref:`auto_csrf_checking` for information about how to secure your
    application automatically against CSRF attacks.

    .. versionadded:: 1.4a2

    .. versionchanged:: 1.7a1
       A CSRF token passed in the query string of the request is no longer
       considered valid. It must be passed in either the request body or
       a header.

    .. versionchanged:: 1.9
       Moved from :mod:`pyramid.session` to :mod:`pyramid.csrf` and updated
       to use the configured :class:`pyramid.interfaces.ICSRFStoragePolicy` to
       verify the CSRF token.

    """
    supplied_token = ""
    # We first check the headers for a csrf token, as that is significantly
    # cheaper than checking the POST body
    if header is not None:
        supplied_token = request.headers.get(header, "")

    # If this is a POST/PUT/etc request, then we'll check the body to see if it
    # has a token. We explicitly use request.POST here because CSRF tokens
    # should never appear in an URL as doing so is a security issue. We also
    # explicitly check for request.POST here as we do not support sending form
    # encoded data over anything but a request.POST.
    if supplied_token == "" and token is not None:
        supplied_token = request.POST.get(token, "")

    policy = request.registry.getUtility(ICSRFStoragePolicy)
    if not policy.check_csrf_token(request, text_(supplied_token)):
        if raises:
            raise BadCSRFToken('check_csrf_token(): Invalid token')
        return False
    return True


def check_csrf_origin(request, trusted_origins=None, raises=True):
    """ Taken from
    https://github.com/Pylons/pyramid/blob/3ee04cc62205b10eb9041b0df5e156936765202f/pyramid/csrf.py#L244

    Check the ``Origin`` of the request to see if it is a cross site request or
    not.

    If the value supplied by the ``Origin`` or ``Referer`` header isn't one of the
    trusted origins and ``raises`` is ``True``, this function will raise a
    :exc:`pyramid.exceptions.BadCSRFOrigin` exception, but if ``raises`` is
    ``False``, this function will return ``False`` instead. If the CSRF origin
    checks are successful this function will return ``True`` unconditionally.

    Additional trusted origins may be added by passing a list of domain (and
    ports if non-standard like ``['example.com', 'dev.example.com:8080']``) in
    with the ``trusted_origins`` parameter. If ``trusted_origins`` is ``None``
    (the default) this list of additional domains will be pulled from the
    ``pyramid.csrf_trusted_origins`` setting.

    Note that this function will do nothing if ``request.scheme`` is not
    ``https``.

    .. versionadded:: 1.7

    .. versionchanged:: 1.9
       Moved from :mod:`pyramid.session` to :mod:`pyramid.csrf`

    """
    def _fail(reason):
        if raises:
            raise BadCSRFOrigin(reason)
        else:
            return False

    if request.scheme == "https":
        # Suppose user visits http://example.com/
        # An active network attacker (man-in-the-middle, MITM) sends a
        # POST form that targets https://example.com/detonate-bomb/ and
        # submits it via JavaScript.
        #
        # The attacker will need to provide a CSRF cookie and token, but
        # that's no problem for a MITM when we cannot make any assumptions
        # about what kind of session storage is being used. So the MITM can
        # circumvent the CSRF protection. This is true for any HTTP connection,
        # but anyone using HTTPS expects better! For this reason, for
        # https://example.com/ we need additional protection that treats
        # http://example.com/ as completely untrusted. Under HTTPS,
        # Barth et al. found that the Referer header is missing for
        # same-domain requests in only about 0.2% of cases or less, so
        # we can use strict Referer checking.

        # Determine the origin of this request
        origin = request.headers.get("Origin")
        if origin is None:
            origin = request.referrer

        # Fail if we were not able to locate an origin at all
        if not origin:
            return _fail("Origin checking failed - no Origin or Referer.")

        # Parse our origin so we we can extract the required information from
        # it.
        originp = urlparse.urlparse(origin)

        # Ensure that our Referer is also secure.
        if originp.scheme != "https":
            return _fail(
                "Referer checking failed - Referer is insecure while host is "
                "secure."
            )

        # Determine which origins we trust, which by default will include the
        # current origin.
        if trusted_origins is None:
            trusted_origins = aslist(
                request.registry.settings.get(
                    "pyramid.csrf_trusted_origins", [])
            )

        if request.host_port not in set(["80", "443"]):
            trusted_origins.append("{0.domain}:{0.host_port}".format(request))
        else:
            trusted_origins.append(request.domain)

        # Actually check to see if the request's origin matches any of our
        # trusted origins.
        if not any(is_same_domain(originp.netloc, host)
                   for host in trusted_origins):
            reason = (
                "Referer checking failed - {0} does not match any trusted "
                "origins."
            )
            return _fail(reason.format(origin))

    return True
