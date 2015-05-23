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
        print('Solo command "{cmd}" was not found.'.format(cmd=args.command))
        sys.exit(1)

    cmd(args)


def init_cmd(args):
    print ("Init!\n")


CLI_COMMANDS = {
    'init': init_cmd,
}