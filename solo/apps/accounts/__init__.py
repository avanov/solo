from solo import Configurator


def includeme(config: Configurator):
    config.include_api_specs(__name__, 'api/specs.raml')
