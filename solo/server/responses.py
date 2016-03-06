import json
from typing import Optional, Any, List, Dict, TypeVar

from aiohttp import web


JsonApiPayload = TypeVar('JsonApiPayload', Dict[str, Any],
                                           List[Dict[str, Any]])


def ok(data: Optional[JsonApiPayload] = None) -> web.Response:
    if data is None:
        data = {}
    return _response(200, data)


def _response(status: int, data: JsonApiPayload) -> web.Response:
    """ Generate a final response in JSON API format:

    * http://jsonapi.org/format/#document-top-level
    * http://jsonapi.org/format/#document-resource-identifier-objects
    """
    data = {
        'data': data,
        'jsonapi': {'version': '1.0'}
    }
    return web.Response(status=status, text=json.dumps(data),
                        content_type='application/vnd.api+json')
