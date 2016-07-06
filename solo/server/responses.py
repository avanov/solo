import json
from typing import Optional, Any, List, Dict, TypeVar

from aiohttp.web import Response


JsonApiPayload = TypeVar('JsonApiPayload', Dict[str, Any],
                                           List[Dict[str, Any]])

encode_json = json.dumps


def ok(data: Optional[JsonApiPayload] = None) -> Response:
    if data is None:
        data = {}
    return _response(200, data)


def _response(status: int, data: JsonApiPayload) -> Response:
    """ Generate a final response in JSON API format:

    * http://jsonapi.org/format/#document-top-level
    * http://jsonapi.org/format/#document-resource-identifier-objects
    """
    data = {
        'data': data,
        'jsonapi': {'version': '1.0'}
    }
    return Response(status=status,
                    text=encode_json(data),
                    content_type='application/vnd.api+json',
                    charset='utf-8')
