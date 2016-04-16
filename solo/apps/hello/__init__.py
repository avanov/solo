from solo.configurator import Configurator


def includeme(config: Configurator):
    config.router.add_route('solo.hello', '/hello')
