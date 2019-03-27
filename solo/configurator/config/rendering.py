import json
from typing import Dict, Any

from solo.server.app import App
from solo.server.request import Request
from solo.server.response import _response_jsonapi, response_json, Response


json_encode = json.dumps


class JsonApiRendererFactory:
    def __init__(self, name: str):
        self.name = name

    def __call__(self, request: Request, view_response: Dict[str, Any]) -> Response:
        return _response_jsonapi(200, view_response)


class JsonRendererFactory:
    def __init__(self, name: str):
        self.name = name

    def __call__(self, request: Request, view_response: Dict[str, Any]) -> Response:
        return response_json(200, view_response)


class StringRendererFactory:
    def __init__(self, name: str):
        self.name = name

    def __call__(self, request: Request, view_response: Any) -> Response:
        return Response(text=str(view_response),
                        content_type='text/plain',
                        charset='utf-8',
                        status=200)


BUILTIN_RENDERERS = {
    'json': JsonRendererFactory,
    'jsonapi': JsonApiRendererFactory,
    'string': StringRendererFactory,
}


class RenderingConfigurator:

    def __init__(self, app: App):
        self.app = app
        self.renderers = {}

    def add_renderer(self, name: str, factory) -> None:
        self.renderers[name] = factory

    def get_renderer(self, name: str):
        try:
            template_suffix = name.rindex(".")
        except ValueError:
            # period is not found
            renderer_name = name
        else:
            renderer_name = name[template_suffix:]

        try:
            return self.renderers[renderer_name](name)
        except KeyError:
            raise ValueError(f'No such renderer factory {renderer_name}')
