from solo import http_endpoint, http_defaults


@http_defaults(route_name='solo.hello')
class HelloWorld:

    def __init__(self, request):
        self.request = request

    @http_endpoint(request_method='GET')
    async def get(self):
        return "Hello World!"
