from typing import Mapping, NamedTuple, Any

import routes


class App(NamedTuple):
    route_map: routes.Mapper
    dbengine: Any
    memstore: Any

    async def __call__(self, scope: Mapping[str, str], receive, send):
        result = self.route_map.match(scope['path'])
        print(result)
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'text/plain'],
            ]
        })
        await send({
            'type': 'http.response.body',
            'body': b'Hello, from uviapp!',
        })

    # These are temporary until aiohttp is ditched
    async def shutdown(self):
        return

    async def cleanup(self):
        return