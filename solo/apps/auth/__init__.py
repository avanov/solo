from solo import Configurator

from .providers import enable_provider


def includeme(config: Configurator):
    config.include_api_specs(__name__, 'api/specs.raml')
    config.add_directive(enable_provider)
