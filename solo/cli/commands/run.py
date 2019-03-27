import argparse

import uvicorn
import logging
import sys

from solo.server.startup import application_entrypoint
from solo.asyncio import configure_io
from solo.config.app import Config


def setup(subparsers: argparse._SubParsersAction):
    sub = subparsers.add_parser('run', help='Run solo application')
    sub.set_defaults(func=entrypoint_cli_run)
    return sub


def entrypoint_cli_run(args: argparse.Namespace,
                       solo_cfg: Config) -> None:
    """ Run project instance.
    """
    log = logging.getLogger('solo')
    loop = configure_io(solo_cfg)

    with application_entrypoint(loop, solo_cfg) as app_manager:
        uvicorn.run(
            app_manager,
            debug=solo_cfg.debug,
            logger=logging.getLogger(f'solo:runtime:{solo_cfg.server.runner.value}'),
            loop=solo_cfg.server.event_loop.value,
            host=solo_cfg.server.host,
            port=solo_cfg.server.port
        )

    loop.close()
    log.info('Done.')
    sys.exit(0)
