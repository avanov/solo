import logging
from typing import List

import venusian


log = logging.getLogger(__name__)


class register_model:
    venusian = venusian

    def __init__(self, **settings):
        self.__dict__.update(settings)

    def __call__(self, wrapped):
        settings = self.__dict__.copy()
        depth = settings.pop('_depth', 0)

        def callback(scanner, name, obj):
            log.debug("Registered model: {} {}".format(name, obj))

        info = self.venusian.attach(wrapped, callback, category='solo', depth=depth + 1)
        return wrapped
