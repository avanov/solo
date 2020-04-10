""" This file is taken from https://github.com/aio-libs/aiohttp-session
for backward-compatibility, and then modified. It's going to be removed at some point.
"""

import json
import time
import uuid

from collections.abc import MutableMapping
from http.cookies import SimpleCookie
from typing import Optional, Awaitable, Dict, Any, Callable, Mapping

import aioredis
from pyrsistent import pmap

from solo.server.request import Request
from solo.server.response import Response
from solo.server.statuses import HttpStatus
from solo.types import IO


class Session(MutableMapping):

    def __init__(self,
        identity: Optional[str], *,
        data: Dict,
        new: bool,
        max_age: Optional[int] = None
    ):
        self._changed = False
        self._mapping: Dict[str, Any] = {}
        self._identity = identity if data != {} else None
        self._new = new
        self._new = new if data != {} else True
        self._max_age = max_age
        created: Optional = data.get('created', None) if data else None
        session_data = data.get('session', None) if data else None
        now = int(time.time())
        age: int = now - created if created else now
        if max_age is not None and age > max_age:
            session_data: Optional[Dict] = None
        if self._new or created is None:
            self._created = now
        else:
            self._created = created

        if session_data is not None:
            self._mapping.update(session_data)

    def __repr__(self) -> str:
        return '<{} [new:{}, changed:{}, created:{}] {!r}>'.format(
            self.__class__.__name__, self.new, self._changed,
            self.created, self._mapping)

    @property
    def new(self) -> bool:
        return self._new

    @property
    def identity(self) -> Optional[str]:
        return self._identity

    @property
    def created(self) -> Optional:
        return self._created

    @property
    def empty(self) -> bool:
        return not bool(self._mapping)

    @property
    def max_age(self) -> Optional[int]:
        return self._max_age

    @max_age.setter
    def max_age(self, value):
        self._max_age = value

    def changed(self):
        self._changed = True

    def invalidate(self) -> None:
        self._changed = True
        self._mapping = {}

    def set_new_identity(self, identity):
        if not self._new:
            raise RuntimeError(
                "Can't change identity for a session which is not new")

        self._identity = identity

    def __len__(self) -> int:
        return len(self._mapping)

    def __iter__(self):
        return iter(self._mapping)

    def __contains__(self, key):
        return key in self._mapping

    def __getitem__(self, key):
        return self._mapping[key]

    def __setitem__(self, key, value):
        self._mapping[key] = value
        self._changed = True

    def __delitem__(self, key):
        del self._mapping[key]
        self._changed = True


SESSION_KEY = 'solo_session'
STORAGE_KEY = 'solo_session_storage'


async def get_session(request: Request) -> Session:
    session = request.get(SESSION_KEY)
    if session is None:
        storage = request.get(STORAGE_KEY)
        if storage is None:
            raise RuntimeError(
                "Install aiohttp_session middleware "
                "in your aiohttp.web.Application")
        else:
            session = await storage.load_session(request)
            if not isinstance(session, Session):
                raise RuntimeError(
                    "Installed {!r} storage should return session instance "
                    "on .load_session() call, got {!r}.".format(storage,
                                                                session))
            request[SESSION_KEY] = session
    return session


async def new_session(request: Request):
    storage = request.get(STORAGE_KEY)
    if storage is None:
        raise RuntimeError(
            "Install aiohttp_session middleware "
            "in your aiohttp.web.Application")
    else:
        session = await storage.new_session()
        if not isinstance(session, Session):
            raise RuntimeError(
                "Installed {!r} storage should return session instance "
                "on .load_session() call, got {!r}.".format(storage, session))
        request[SESSION_KEY] = session
    return session


def setup(storage: 'SessionStore') -> Callable[[Request], IO[Session]]:
    async def factory(request: Request):
        request[STORAGE_KEY] = storage
        raise_response = False
        try:
            response = await handler(request)
        except HttpStatus as exc:
            response = exc
            raise_response = True

        if response.prepared:
            raise RuntimeError(
                "Cannot save session data into prepared response")
        session = request.get(SESSION_KEY)
        if session is not None:
            if session._changed:
                await storage.save_session(request, response, session)
        if raise_response:
            raise response
        return response

    return factory


class SessionStore:
    """Redis storage"""

    def __init__(self,
                 redis_pool: aioredis.commands.Redis, *,
                 cookie_name: str = "solo-session",
                 secure: bool = None,
                 httponly: bool = True,
                 domain = None,
                 max_age = None,
                 path = '/',
                 key_factory = lambda: uuid.uuid4().hex,
                 encoder = json.dumps, decoder=json.loads):
        self._cookie_name = cookie_name
        self._cookie_params = dict(domain=domain,
                                   max_age=max_age,
                                   path=path,
                                   secure=secure,
                                   httponly=httponly)
        self._max_age = max_age
        self._encoder = encoder
        self._decoder = decoder

        self._key_factory = key_factory
        self._redis = redis_pool

    @property
    def cookie_name(self):
        return self._cookie_name

    @property
    def max_age(self):
        return self._max_age

    @property
    def cookie_params(self):
        return self._cookie_params

    async def new_session(self) -> Session:
        return Session(None, data=None, new=True, max_age=self.max_age)

    async def load_session(self, request: Request) -> Session:
        cookie = self.load_cookie(request)
        if cookie:
            with await self._redis as conn:
                key = str(cookie)
                data = await conn.get(self.cookie_name + '_' + key)
                if data is None:
                    return Session(None, data=None,
                                   new=True, max_age=self.max_age)
                data = data.decode('utf-8')
                try:
                    data = self._decoder(data)
                except ValueError:
                    data = None
                return Session(key, data=data, new=False, max_age=self.max_age)
        else:
            return Session(None, data=None, new=True, max_age=self.max_age)

    def load_cookie(self, request: Request) -> Mapping[str, Any]:
        cookies = SimpleCookie(request.headers.get('cookie', ''))
        cookie = cookies.get(self._cookie_name) or pmap()
        return cookie

    async def save_session(self, request: Request, response, session):
        key = session.identity
        if key is None:
            key = self._key_factory()
            self.save_cookie(response, key,
                             max_age=session.max_age)
        else:
            if session.empty:
                self.save_cookie(response, '',
                                 max_age=session.max_age)
            else:
                key = str(key)
                self.save_cookie(response, key,
                                 max_age=session.max_age)

        data = self._encoder(self._get_session_data(session))
        with await self._redis as conn:
            max_age = session.max_age
            expire = max_age if max_age is not None else 0
            await conn.set(self.cookie_name + '_' + key, data, expire=expire)

    def save_cookie(self, response: Response, cookie_data, *, max_age=None):
        params = dict(self._cookie_params)
        if max_age is not None:
            params['max_age'] = max_age
            params['expires'] = time.strftime(
                "%a, %d-%b-%Y %T GMT",
                time.gmtime(time.time() + max_age))
        if not cookie_data:
            response.del_cookie(
                self._cookie_name,
                domain=params["domain"],
                path=params["path"],
                )
        else:
            response.set_cookie(self._cookie_name, cookie_data, **params)

    def _get_session_data(self, session: Session):
        if not session.empty:
            data = {
                'created': session.created,
                'session': session._mapping
            }
        else:
            data = {}
        return data