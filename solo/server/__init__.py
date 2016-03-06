import asyncio
from typing import Any, Dict, Tuple

from aiohttp import web

from . import db


async def init_app(loop: asyncio.AbstractEventLoop,
                   config: Dict[str, Any]) -> web.Application:
    app = web.Application(loop=loop,
                          debug=config['debug'])
    # Setup routes
    # ------------
    #app.router.add_route("GET", "/probabilities/{attrs:.+}",
    #                     probabilities.handlers.handler)

    # Setup database connection pool
    # ------------------------------
    engine = await db.setup_database(loop, config)
    setattr(app, 'dbengine', engine)
    return app
