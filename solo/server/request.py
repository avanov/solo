from typing import NamedTuple, Any, Mapping

from pyrsistent import pmap
from pyrsistent.typing import PMap

from .definitions import HttpMethod


class Request(NamedTuple):
    method: HttpMethod = HttpMethod.GET
    path: str = '/'
    url_params: Mapping[str, str] = pmap({})
    qs_params: Mapping[str, str] = pmap({})
    headers: PMap[str, str] = pmap({})
