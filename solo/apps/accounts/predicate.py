from aiohttp.web_reqrep import Request
from .util import get_user


class PermissionPredicate:
    def __init__(self, val, config):
        config.app.setdefault('permissions', set()).add(val)
        self.val = val

    def text(self):
        return 'permission = {}'.format(self.val)

    phash = text

    async def __call__(self, context, request: Request) -> bool:
        # TODO: retrieve user permissions and check against self.val
        return False
