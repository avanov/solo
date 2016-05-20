""" Place for Console Scripts.
"""
import argparse
import asyncio
import logging
import logging.config
import sys
from typing import List

from pkg_resources import get_distribution

from solo.integrations.alembic import integrate_alembic_cli
from solo.server import init_webapp
from .util import parse_app_config


def run_cmd(args: argparse.Namespace, unknown: List[str]):
    """ Run project instance.
    """
    config = parse_app_config(args.config)

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


def main(args=None, stdout=None):
    parser = argparse.ArgumentParser(description='Manage Solo projects.')
    parser.add_argument('-V', '--version', action='version',
                        version='Solo {}'.format(get_distribution("solo").version))
    subparsers = parser.add_subparsers(title='sub-commands',
                                       description='valid sub-commands',
                                       help='additional help')

    # $ solo run <config>
    # ---------------------------
    run = subparsers.add_parser('run', help='Run solo application')
    run.set_defaults(func=run_cmd)

    # $ solo db [args]
    # ---------------------------
    integrate_alembic_cli(subparsers)

    # Common arguments
    # ----------------
    _add_common_arguments(subparsers)

    # Parse
    # ---------------------------
    if args is None:
        args = sys.argv[1:]
    args = parser.parse_args(args)
    args.func(args)


def _add_common_arguments(subparsers: argparse._SubParsersAction):
    """ Recursively search for innermost parsers and add common arguments to their arguments.
    The goal is to allow common arguments be specified after all subcommand-specific arguments,
    i.e. to be able to invoke
    $ solo db revision [--solocfg SOLOCFG]
    instead of
    $ solo [--solocfg SOLOCFG] db revision
    without having to manually specify parent parsers as described at
    # https://docs.python.org/3/library/argparse.html#parents
    """
    for sp in subparsers.choices.values():  # type: argparse.ArgumentParser
        if sp._subparsers:
            for action in sp._subparsers._actions:
                if not isinstance(action, argparse._SubParsersAction):
                    continue
                # Traverse to the inner subparser
                _add_common_arguments(action)
        else:
            sp.add_argument("--solocfg", default='solocfg.yml', help="path to a YAML config (default ./solocfg.yml).")
