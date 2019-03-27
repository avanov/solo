import json
from typing import Optional, Any, List, Dict, TypeVar, NamedTuple


JsonApiPayload = TypeVar('JsonApiPayload', Dict[str, Any],
                                           List[Dict[str, Any]])

encode_json = json.dumps


class Response(NamedTuple):
    status: int
    text: str
    content_type: str
    charset: str



def ok(data: Optional[JsonApiPayload] = None) -> Response:
    if data is None:
        data = {}
    return _response_jsonapi(200, data)


def _response_jsonapi(status: int, data: JsonApiPayload) -> Response:
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


def response_json(status: int, data: JsonApiPayload) -> Response:
    """ Generate a simple JSON response format:
    """
    return Response(status=status,
                    text=encode_json(data),
                    content_type='application/json',
                    charset='utf-8')
