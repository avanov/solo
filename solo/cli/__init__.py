""" Place for Console Scripts.
"""
import argparse
import sys
from pkg_resources import get_distribution

import yaml


def main(args=None, stdout=None):
    cli_parser = argparse.ArgumentParser(description='Compile plim source files into mako files.')
    cli_parser.add_argument('command', help="Solo command")
    cli_parser.add_argument('-V', '--version', action='version',
                            version='Solo {}'.format(get_distribution("solo").version))

    if args is None:
        args = sys.argv[1:]
    args = cli_parser.parse_args(args)
    try:
        cmd = CLI_COMMANDS[args.command]
    except KeyError:
        sys.exit('Solo command "{cmd}" was not found. Use one of the following: \n- {available}'.format(
            cmd=args.command,
            available='\n- '.join([c for c in CLI_COMMANDS.keys()])
        ))

    cmd(args)


def init_cmd(args):
    """ Create an initial config in the current directory.
    """
    args = argparse.ArgumentParser(description='Compile plim source files into mako files.')


INIT_CONFIG = """---
# Solo App Config
"""


CLI_COMMANDS = {
    'init': init_cmd,
}
