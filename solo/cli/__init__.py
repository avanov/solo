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


def main(args=None, stdout=None):
    cli_parser = argparse.ArgumentParser(description='Manage solo projects.')
    cli_parser.add_argument('command', help="Solo command")
    cli_parser.add_argument('cmd_options', type=str, nargs='*',
                            help='command-specific options')
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

    cmd(args.cmd_options)


def run_cmd(args: List[str]):
    """ Run project instance.
    """
    config = parse_app_config(args)

    logging.config.dictConfig(config['logging'])
    log = logging.getLogger('solo')

    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=config['debug'])

    with loop.run_until_complete(init_webapp(loop, config)) as app:
        # handler = app.make_handler()
        #f = loop.create_server(handler, config['server']['host'], config['server']['port'])
        app.create_server()
        log.debug('Serving on {}'.format(app.server.sockets[0].getsockname()))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            log.debug('[SIGINT] A command to shut down the server has been received...')

    loop.close()
    log.debug('Done.')
    sys.exit(0)


INIT_CONFIG = """---
# Solo App Config
"""


CLI_COMMANDS = {
    'run': run_cmd,
}


def parse_app_config(argv: List[str]) -> Dict[str, Any]:
    p = argparse.ArgumentParser()
    p.add_argument("config", help="path to a YAML config.")
    args = p.parse_args(argv)
    with Path(args.config).open() as f:
        config = yaml.load(f.read())
    return config
