import routes


route_map = routes.Mapper()
route_map.connect("home", "/", controller=object(), action="index", blah=True)
route_map.connect("home", "/users", controller="users", action="users")


class App:
    def __init__(self, scope):
        print('Scope', scope)
        self.scope = scope

    async def __call__(self, receive, send):
        result = route_map.match(self.scope['path'])
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
