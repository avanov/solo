import json

from aiohttp.web import Response


json_encode = json.dumps


class JsonRendererFactory(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, request, view_response):
        return Response(text=json_encode(view_response),
                        content_type='application/json',
                        charset='utf-8',
                        status=200)


class StringRendererFactory(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, request, view_response):
        return Response(text=view_response,
                        content_type='text/plain',
                        charset='utf-8',
                        status=200)


BUILTIN_RENDERERS = {
    'json': JsonRendererFactory,
    'string': StringRendererFactory,
}


class RenderingConfigurator:

    def __init__(self):
        self.renderers = {}

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
