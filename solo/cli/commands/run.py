import argparse

import uvicorn
import logging
import sys

from solo.server.startup import application_entrypoint
from solo.asyncio import configure_io
from solo.config.app import Config, RunnerType


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
        if solo_cfg.server.runner is RunnerType.UVICORN:
            uvicorn.run(
                app_manager,
                debug=solo_cfg.debug,
                logger=logging.getLogger(f'solo:runtime:{solo_cfg.server.runner.value}'),
                loop=solo_cfg.server.event_loop.value,
                host=solo_cfg.server.host,
                port=solo_cfg.server.port
            )
        else:
            socket_name = app_manager.server.sockets[0].getsockname()
            log.info(f'Serving on {socket_name}')
            try:
                app_manager.loop.run_forever()
            except KeyboardInterrupt:
                log.info('[SIGINT] A command to shut down the server has been received...')

    loop.close()
    log.info('Done.')
    sys.exit(0)
