import asyncio
from asyncio import AbstractEventLoop

import uvloop
import logging

from solo.config.app import Config, EventLoopType


log = logging.getLogger(__name__)


def configure_io(solo_cfg: Config) -> AbstractEventLoop:
    if solo_cfg.server.event_loop is EventLoopType.UVLOOP:
        log.debug('Switching to uvloop asyncio implementation')
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.set_debug(solo_cfg.debug)
    return loop
