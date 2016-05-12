import asyncio
import logging

from solo.server import init_webapp
from solo.cli import parse_app_config

from sqlalchemy import pool, create_engine


log = logging.getLogger(__name__)


def _config_from_alembic(alembic_config):
    return parse_app_config([alembic_config.get_section_option('solo', 'config')])


def collect_metadata(alembic_config):
    from solo.server.model import metadata

    loop = asyncio.get_event_loop()
    solo_config = _config_from_alembic(alembic_config)
    loop.set_debug(enabled=solo_config['debug'])
    app = loop.run_until_complete(init_webapp(loop, solo_config))
    # TODO: implement as signal handlers
    # Close database pool (could be implemented better with signals)
    if hasattr(app, 'dbengine'):
        log.debug('Closing database connections...')
        app.dbengine.terminate()
        loop.run_until_complete(app.dbengine.wait_closed())

    # Close memstore pool
    if hasattr(app, 'memstore'):
        log.debug('Closing memory store connections...')
        loop.run_until_complete(app.memstore.clear())
    return metadata


def get_run_migrations_online(alembic_config, target_metadata, context):
    def run_migrations_online():
        """Run migrations in 'online' mode.

        In this scenario we need to create an Engine
        and associate a connection with the context.

        """
        solo_config = _config_from_alembic(alembic_config)
        dbconf = solo_config['postgresql']
        connectable = create_engine(
            'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}'.format(**dbconf),
            poolclass=pool.NullPool)

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()

    return run_migrations_online
