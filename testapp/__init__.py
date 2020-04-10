from solo import Configurator


def includeme(config: Configurator) -> None:
    """ Setup your application here.
    """
    config.router.add_route('index', '/')
