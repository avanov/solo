import asyncio
from typing import Dict, Any
from alembic.config import Config
from solo import init_webapp


def alembic_config_from_solo(solo_cfg: Dict[str, Any]) -> Config:
    """ Generates valid Alembic configuration from a given Solo configuration.
    The return value can be passed to `alembic commands API <http://alembic.readthedocs.io/en/latest/api/commands.html>`_.

    :param solo_cfg: Solo configuration
    :return: Alembic configuration
    """
    alembic_cfg = Config(ini_section='main')

    # path to migration scripts
    alembic_cfg.set_main_option("script_location", "solo.integrations:alembic")

    # template used to generate migration files
    alembic_cfg.set_main_option("file_template", "%%(rev)s_%%(slug)s")

    # max length of characters to apply to the "slug" field
    alembic_cfg.set_main_option("truncate_slug_length", "40")

    # set to 'true' to run the environment during
    # the 'revision' command, regardless of autogenerate
    alembic_cfg.set_main_option("revision_environment", "false")

    # set to 'true' to allow .pyc and .pyo files without
    # a source .py file to be detected as revisions in the
    # versions/ directory
    alembic_cfg.set_main_option("sourceless", "false")

    # version location specification; this defaults
    # to .alembic/versions.  When using multiple version
    # directories, initial revisions must be specified with --version-path
    # version_locations = %(here)s/bar %(here)s/bat .alembic/versions
    version_locations = ' '.join(('{}:migrations'.format(app) for app in solo_cfg['apps']))
    alembic_cfg.set_main_option("version_locations", version_locations)

    # the output encoding used when revision files
    # are written from script.py.mako
    alembic_cfg.set_main_option("output_encoding", "utf-8")

    dbconf = solo_cfg['postgresql']
    alembic_cfg.set_main_option('sqlalchemy.url',
                                'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}'.format(**dbconf))

    alembic_cfg.attributes['target_metadata'] = collect_metadata(solo_cfg)

    return alembic_cfg


def collect_metadata(solo_cfg: Dict[str, Any]):
    from solo.server.model import metadata

    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=solo_cfg['debug'])
    with loop.run_until_complete(init_webapp(loop, solo_cfg)) as app:
        pass
    return metadata
