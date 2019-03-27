import argparse
import asyncio
import logging
import sys

from solo import init_webapp
from solo.config.app import Config


def setup(subparsers):
    sub = subparsers.add_parser('run', help='Run solo application')
    sub.set_defaults(func=main)
    return sub


def main(args: argparse.Namespace,
         solo_cfg: Config) -> None:
    """ Run project instance.
    """
    log = logging.getLogger('solo')
    loop = asyncio.get_event_loop()
    loop.set_debug(solo_cfg.debug)

    with loop.run_until_complete(init_webapp(loop, solo_cfg)) as app:
        app.create_server()
        socket_name = app.server.sockets[0].getsockname()
        log.debug(f'Serving on {socket_name}')
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            log.debug('[SIGINT] A command to shut down the server has been received...')

    loop.close()
    log.debug('Done.')
    sys.exit(0)
