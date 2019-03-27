from typing import Tuple, Awaitable, Mapping, Type, Iterator, Optional

import lowhaio
from pyrsistent import pmap

from solo.server.io_manager import AIOManager
from.server.definitions import HttpMethod


class TestClient:
    def __init__(self, app_manager: AIOManager, pool=lowhaio.Pool):
        self.app_manager = app_manager
        self.make_raw_request, self.close = pool()

    def get(self, url: str,
                   headers: Mapping[str, str] = pmap({}),
                   payload: Optional[Type] = None) -> Awaitable[Tuple[int, Mapping, Iterator]]:
        return self.make_request(
            url=url,
            method=HttpMethod.GET,
            headers=headers,
            payload=payload,
        )
    post = get

    async def make_request(self,
                   url: str,
                   method: HttpMethod,
                   headers: Mapping[str, str] = pmap({}),
                   payload: Optional[Type] = None) -> Tuple[int, Mapping, Iterator]:
        iter_headers = (
            (k.lower().encode('utf-8'), v.encode('utf-8'))
            for k, v in headers.items()
        )
        server = self.app_manager.server
        status_code, headers, response_body = await self.make_raw_request(
            method.value.encode('utf-8'),
            f'http://{server.host}:{server.port}{url}',
            headers=iter_headers,
            body=lowhaio.streamed('{}'),
        )
        return status_code, headers, response_body
