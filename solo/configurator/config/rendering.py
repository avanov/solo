import json

from aiohttp.web import Response


json_encode = json.dumps


class JsonRendererFactory(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, request, view_response):
        response = request.response
        response.content_type = 'application/json'
        response.content = json_encode(view_response)
        return Response(text=response.content,
                        content_type=response.content_type,
                        charset='utf-8',
                        status=response.status_code)


class StringRendererFactory(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, request, view_response):
        response = request.response
        response.content_type = 'text/plain; charset=utf-8'
        response.content = view_response
        return response


BUILTIN_RENDERERS = {
    'json': JsonRendererFactory,
    'string': StringRendererFactory,
}


class RenderingConfiguratorMixin(object):

    def add_renderer(self, name, factory):
        self.renderers[name] = factory

    def get_renderer(self, name):
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
            raise ValueError('No such renderer factory {}'.format(renderer_name))
