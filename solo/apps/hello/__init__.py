from solo.configurator import Configurator


def includeme(config: Configurator):
    config.add_route('solo.hello', '/hello')
