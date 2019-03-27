from typing import Optional, Tuple

from solo.server.statuses import Http4xx
from solo.server.definitions import HttpMethod
from solo.server.runtime.dependencies import Runtime
from ...server.request import Request
from .util import as_sorted_tuple


class RequestMethodPredicate:
    def __init__(self, val: Tuple[HttpMethod, ...], config, raises: Optional[Http4xx] = None):
        """ Predicates are constructed at ``solo.configurator.config.util.PredicateList.make()``

        :param val: value passed to view_config/view_defaults
        :param config:
        """
        request_method = as_sorted_tuple(val)
        if HttpMethod.GET in request_method and HttpMethod.HEAD not in request_method:
            # GET implies HEAD too
            request_method = as_sorted_tuple(request_method + (HttpMethod.HEAD,))
        self.val = request_method
        self.raises = raises

    def text(self) -> str:
        return 'request_method = %s' % (','.join(x.value for x in self.val))

    phash = text

    async def __call__(self, runtime: Runtime, request: Request) -> bool:
        return request.method in self.val
