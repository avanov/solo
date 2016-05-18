""" Place for Console Scripts.
"""
import argparse
import asyncio
import logging
import logging.config
import sys
from typing import Any, List, Dict
from pathlib import Path

from pkg_resources import get_distribution
import yaml

from solo.server import init_webapp


def run_cmd(args: argparse.Namespace):
    """ Run project instance.
    """
    with Path(args.config).open() as f:
        config = yaml.load(f.read())

    logging.config.dictConfig(config['logging'])
    log = logging.getLogger('solo')

    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=config['debug'])

    with loop.run_until_complete(init_webapp(loop, config)) as app:
        app.create_server()
        log.debug('Serving on {}'.format(app.server.sockets[0].getsockname()))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            log.debug('[SIGINT] A command to shut down the server has been received...')

    loop.close()
    log.debug('Done.')
    sys.exit(0)


def db_cmd(args: argparse.Namespace):
    pass


def main(args=None, stdout=None):
    parser = argparse.ArgumentParser(description='Manage solo projects.')
    parser.add_argument('-V', '--version', action='version',
                        version='Solo {}'.format(get_distribution("solo").version))
    subparsers = parser.add_subparsers(title='sub-commands',
                                       description='valid sub-commands',
                                       help='additional help')

    # $ solo run <config>
    # ---------------------------
    run = subparsers.add_parser('run', help='Run solo application')
    run.add_argument("config", help="path to a YAML config.")
    run.set_defaults(func=run_cmd)

    # $ solo db [args]
    # ---------------------------
    db = subparsers.add_parser('db', help='Database commands integrated with Alembic CLI')
    db.add_argument('alembic_cmd', type=str, nargs='*',
                    help='alembic-specific command')
    db.set_defaults(func=db_cmd)

    # Parse
    # ---------------------------
    if args is None:
        args = sys.argv[1:]
    args = parser.parse_args(args)
    args.func(args)



INIT_CONFIG = """---
# Solo App Config
"""
