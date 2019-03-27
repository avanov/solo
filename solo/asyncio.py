import asyncio
from asyncio import AbstractEventLoop

import logging

from solo.config.app import Config, EventLoopType


log = logging.getLogger(__name__)


def configure_io(solo_cfg: Config) -> AbstractEventLoop:
    decide_event_loop_policy(solo_cfg)
    loop = asyncio.get_event_loop()
    loop.set_debug(solo_cfg.debug)
    return loop


def decide_event_loop_policy(solo_cfg: Config) -> None:
    """ Select and set event loop implementation.
    """
    if solo_cfg.server.event_loop is EventLoopType.UVLOOP:
        log.debug('Switching to uvloop asyncio implementation')
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    return
