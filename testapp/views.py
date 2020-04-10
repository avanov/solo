from typing import Mapping

from solo import http_endpoint
from solo.server.definitions import HttpMethod


@http_endpoint(route_name='index', request_method=HttpMethod.GET, renderer='json')
def index(request, context) -> Mapping[str, str]:
    return {'hello': 'world'}