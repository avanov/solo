import asyncio
import logging
import urllib.parse
from typing import Mapping, Optional, Dict, Any, Awaitable, Callable

import routes
from pyrsistent import pmap

from solo.server.response import Response
from solo.server.statuses import Http4xx, Http3xx, NotFound
from solo.server.definitions import MatchedRoute, PredicatedHandler
from solo.server.runtime.dependencies import get_handler_deps
from ..request import Request
from ..definitions import HttpMethod, ScopeType, ScopeScheme, ScopeServer, Scope
from solo.server.runtime.dependencies import Runtime
from ...types import IO

logger = logging.getLogger(__name__)


async def handle_request(
    runtime: Runtime,
    route_map: routes.Mapper,
    scope: Mapping[str, Any],
    receive: Callable[[], IO],
    send: Callable[[Mapping[str, Any]], IO]
) -> None:
    scope_ = Scope(
        type=ScopeType(scope['type']),
        scheme=ScopeScheme(scope['scheme']),
        root_path=scope['root_path'],
        server=ScopeServer(host=scope['server'][0],
                           port=scope['server'][1]),
        http_version=scope['http_version'],
        method=HttpMethod(scope['method'].lower()),
        path=scope['path'],
        query_string=scope['query_string'],
        headers=pmap({
            header_tuple[0].decode('utf-8'): header_tuple[1].decode('utf-8')
            for header_tuple in scope['headers']
        })
    )
    result: Optional[Dict[str, Any]] = route_map.match(scope_.path)
    if result is None:
        logger.debug(f'No route was matched for the request scope {scope}')
        await send({
            'type': 'http.response.start',
            'status': 404,
            'headers': [
                [b'content-type', b'text/plain'],
            ]
        })
        await send({
            'type': 'http.response.body',
            'body': b'404 Not Found',
        })
    else:
        matched_route = MatchedRoute(
            controller=result.pop('controller'),
            params=pmap(result),
        )
        request = Request(
            method=scope_.method,
            path=scope_.path,
            url_params=matched_route.params,
            qs_params=pmap(urllib.parse.parse_qs(
                scope_.query_string.decode('utf-8'),
                strict_parsing=True,
                keep_blank_values=True,
                max_num_fields=256,
            )) if scope_.query_string else pmap()
        )
        try:
            response = await call_matched_controller(
                matched_route.controller,
                runtime=runtime,
                request=request
            )
        except (Http4xx, Http3xx) as e:
            status = e.status
            response_body = b''
            content_type = b'text/plain'
        except Exception as e:
            status = 500
            response_body = b'HTTP 500: Internal Server Error'
            content_type = b'text/plain'
        else:
            status = 200
            response_body = response.text.encode('utf-8')
            content_type = response.content_type.encode('utf-8')

        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [
                [b'content-type', content_type],
            ]
        })
        await send({
            'type': 'http.response.body',
            'body': response_body,
            # indicates end of response stream
            'more_body': False
        })


async def call_matched_controller(
    controller: PredicatedHandler,
    runtime: Runtime,
    request: Request
) -> Response:
    for view_item in controller.view_metas:
        for predicate in view_item.predicates:
            if not (await predicate(runtime, request)):
                logger.debug(f'Predicate {predicate} failed for {request.method} {request.path}')
                break
        else:
            # All predicates match
            logger.debug(f'{request.method} {request.path} will be handled by {view_item.view}')
            handler = view_item.view
            context = {}
            rules = controller.rules
            for k, v in request.url_params.items():
                if k in rules:  # match SumType's case
                    context[k] = controller.rules[k].match(v)
                else:  # regular value assignment
                    context[k] = v
            if view_item.attr:
                # handler is a coroutine method of a class
                handler = getattr(handler(request, context), view_item.attr)
                handler_args = ()
            else:
                # handler is a simple coroutine
                handler_args = (request, context)

            coro_deps, handler_deps = get_handler_deps(runtime, handler, request)
            collected = await asyncio.gather(*[x for x in coro_deps.values()])

            # Here we rely on the fact that the order of collected values corresponds
            # to the order of coro_deps:
            # https://docs.python.org/3/library/asyncio-task.html#asyncio.gather
            collected_deps = dict(zip(coro_deps.keys(), collected))

            response = await handler(*handler_args, **handler_deps, **collected_deps)

            if isinstance(response, Response):
                # Do not process standard responses
                return response
            renderer = view_item.renderer
            return renderer(request, response)

    logger.debug(f'All predicates have failed for {request.method} {request.path}')
    raise NotFound()