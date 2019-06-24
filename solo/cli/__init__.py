""" Place for Console Scripts.
"""
import argparse
import asyncio
import logging
import logging.config
import sys
from pathlib import Path

from pkg_resources import get_distribution

from . import commands
from solo.integrations.alembic import integrate_alembic_cli
from solo.config.app import Config, EventLoopType
from .util import parse_app_config, parse_compose_config


def main(args=None, stdout=None) -> None:
    parser = argparse.ArgumentParser(description='Manage Solo projects.')
    parser.add_argument('-V', '--version', action='version',
                        version=f'Solo {get_distribution("solo").version}')
    subparsers = parser.add_subparsers(title='sub-commands',
                                       description='valid sub-commands',
                                       help='additional help',
                                       dest='sub-command')
    # make subparsers required (see http://stackoverflow.com/a/23354355/458106)
    subparsers.required = True

    # $ solo run <config>
    # ---------------------------
    commands.run.setup(subparsers)

    # $ solo db [args]
    # ---------------------------
    integrate_alembic_cli(subparsers, prefix='db')

    # Common arguments
    # ----------------
    _add_common_arguments(subparsers)

    # Parse arguments and config
    # --------------------------
    if args is None:
        args = sys.argv[1:]
    args = parser.parse_args(args)
    solo_cfg = parse_app_config(Path(args.solocfg))

    # Set up and run
    # --------------
    decide_event_loop_policy(solo_cfg)
    logging.config.dictConfig(solo_cfg.logging)
    args.func(args, solo_cfg)


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


def decide_event_loop_policy(solo_cfg: Config) -> None:
    """ Select and set event loop implementation.
    """
    if solo_cfg.server.event_loop is EventLoopType.UVLOOP:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
