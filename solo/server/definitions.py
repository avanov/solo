from enum import Enum
from typing import NamedTuple, Dict, List, Mapping

from pyrsistent.typing import PMap

from solo.configurator.config.routes import ViewMeta
from solo.configurator.config.sums import SumType


class HttpMethod(Enum):
    HEAD = 'head'
    GET = 'get'
    POST = 'post'

    def __lt__(self, other: 'HttpMethod') -> bool:
        return self.value.__lt__(other.value)


class ScopeType(Enum):
    HTTP_REQUEST = 'http'


class ScopeScheme(Enum):
    HTTP = 'http'


class ScopeServer(NamedTuple):
    host: str
    port: int


class Scope(NamedTuple):
    type: ScopeType
    scheme: ScopeScheme
    root_path: str
    server: ScopeServer
    http_version: str
    method: HttpMethod
    path: str
    headers: PMap[str, str]
    query_string: bytes


class PredicatedHandler:
    __slots__ = ('rules', 'view_metas')

    def __init__(self, rules: Dict[str, SumType], view_metas: List[ViewMeta]):
        self.view_metas = view_metas
        self.rules = rules

    def __call__(self, **kw):
        return


class MatchedRoute(NamedTuple):
    controller: PredicatedHandler
    params: Mapping[str, str]