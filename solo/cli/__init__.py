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
    log = logging.getLogger('assignment')

    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=config['debug'])

    app = loop.run_until_complete(init_webapp(loop, config))
    handler = app.make_handler()
    f = loop.create_server(handler, config['server']['host'], config['server']['port'])
    srv = loop.run_until_complete(f)
    log.debug('Serving on {}'.format(srv.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        log.debug('[SIGINT] Shutting down the server gracefully...')
    finally:
        # Close database pool (could be implemented better with signals)
        if hasattr(app, 'dbengine'):
            log.debug('Closing database connections...')
            app.dbengine.terminate()
            loop.run_until_complete(app.dbengine.wait_closed())

        # all the rest
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.shutdown())
        loop.run_until_complete(handler.finish_connections(60.0))
        loop.run_until_complete(app.cleanup())

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
