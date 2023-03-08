import logging
from typing import NamedTuple, Optional, Mapping, Awaitable, Callable, TypeVar, Any

from solo.types import IO
from solo.vendor.old_session.old_session import SessionStore

from solo.configurator.registry import Registry
from solo.server.app import App
from solo.server.handler.http_handler import handle_request
from solo.server.runtime.dependencies import Runtime

log = logging.getLogger(__name__)


T = TypeVar('T')


class AIOManager:
    def __init__(self,
        loop,
        app: App,
        registry: Registry,
    ) -> None:
        self.app = app
        self.config = registry.config
        self.registry = registry
        self.loop = loop
        self.server = None
        self.runtime: Optional[Runtime] = None
        self.do_io: Callable[[IO[T]], T] = self.loop.run_until_complete

    def create_server(self, ssl: Optional[bool] = None):
        log.debug('Creating a new web server...')
        return self.do_io(self.create_server_future(ssl))

    def create_server_future(self, ssl: Optional[bool] = None):
        host = self.config.server.host
        port = self.config.server.port
        return self.loop.create_server(self.runtime.handler, host, port, ssl=ssl)

    def __enter__(self) -> 'AIOManager':
        """ Runs as the step between configuration phase and network serving phase.
        """
        log.info('Entering application IO context...')
        # Setup sessions middleware
        # -------------------------
        db_engine = self.app.dbengine
        memstore = self.do_io(self.app.memstore)

        session_storage = SessionStore(
            memstore,
            cookie_name=self.config.session.cookie_name,
            secure=self.config.session.cookie_secure,
            httponly=self.config.session.cookie_httponly
        )

        class ServerDescription(NamedTuple):
            host: str
            port: int

            def close(self): return

            async def wait_closed(self): return

        self.server = ServerDescription(host=self.config.server.host,
                                        port=self.config.server.port)

        self.runtime = Runtime(
            registry=self.registry,
            dbengine=db_engine,
            memstore=memstore,
            session_storage=session_storage,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """ Runs at the server shutdown phase
        """
        log.debug('Exiting application IO context...')
        if self.runtime:
            # Close memstore pool
            log.debug('Closing memory store connections...')
            self.do_io(self.runtime.memstore.close())

        if self.server:
            log.debug('Stopping server...')
            self.server.close()
            self.do_io(self.server.wait_closed())
        log.debug('Done.')

    async def __call__(self,
        scope: Mapping[str, str],
        receive: Callable[[], IO],
        send: Callable[[Mapping[str, Any]], IO]
    ) -> IO:
        return await handle_request ( runtime   = self.runtime
                                    , route_map = self.app.route_map
                                    , scope     = scope
                                    , receive   = receive
                                    , send      = send )