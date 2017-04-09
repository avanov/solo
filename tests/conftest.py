# """ https://pytest.org/latest/fixture.html#sharing-a-fixture-across-tests-in-a-module-or-class-session
#
# This conftest is a copy of https://github.com/KeepSafe/aiohttp/blob/master/tests/conftest.py
#
# Since there's no a working test suite for aiohttp (https://github.com/sloria/webtest-aiohttp/issues/1),
# we use the same suite as the base framework.
# """
# import asyncio
# import aiohttp
# import collections
# import logging
# import pytest
# import re
# import sys
# import warnings
#
# from solo.testutils import (
#     loop_context, unused_port
# )
#
# from solo.cli.util import parse_app_config
# from solo import init_webapp
#
#

#
# @pytest.yield_fixture
# def create_server(loop):
#     app = handler = srv = None
#     config = parse_app_config('./test_config.yml')  # TODO: move path to outer scope
#
#     async def create(*, debug=False, ssl_ctx=None, proto='http'):
#         nonlocal app, handler, srv, config
#         port = unused_port()
#         app_manager = await init_webapp(loop, config)
#         server_future = app_manager.create_server_future(host='127.0.0.1', port=port, ssl=ssl_ctx)
#         if ssl_ctx:
#             proto += 's'
#         url = "{}://127.0.0.1:{}/".format(proto, port)
#
#         app = app_manager.app
#         handler = app_manager.handler
#         srv = await server_future
#         return app, url
#
#     yield create
#
#
#     async def finish():
#         if hasattr(app, 'dbengine'):
#             app.dbengine.terminate()
#             await app.dbengine.wait_closed()
#
#         if hasattr(app, 'memstore'):
#             await app.memstore.clear()
#
#         await handler.finish_connections()
#         await app.finish()
#         srv.close()
#         await srv.wait_closed()
#
#     loop.run_until_complete(finish())
#
#
# class Client:
#     def __init__(self, session, url):
#         self._session = session
#         self._url = url
#
#     def close(self):
#         self._session.close()
#
#     def get(self, path, **kwargs):
#         url = "{}/{}".format(self._url.rstrip('/'), path.lstrip('/'))
#         return self._session.get(url, **kwargs)
#
#     def post(self, path, **kwargs):
#         url = "{}/{}".format(self._url.rstrip('/'), path.lstrip('/'))
#         return self._session.post(url, **kwargs)
#
#     def delete(self, path, **kwargs):
#         url = "{}/{}".format(self._url.rstrip('/'), path.lstrip('/'))
#         return self._session.delete(url)
#
#     def ws_connect(self, path, **kwargs):
#         url = "{}/{}".format(self._url.rstrip('/'), path.lstrip('/'))
#         return self._session.ws_connect(url, **kwargs)
#
#
# @pytest.yield_fixture
# def create_app_and_client(create_server, loop):
#     client = None
#
#     @asyncio.coroutine
#     def maker(*, server_params=None, client_params=None):
#         nonlocal client
#         if server_params is None:
#             server_params = {}
#         server_params.setdefault('debug', False)
#         server_params.setdefault('ssl_ctx', None)
#         app, url = yield from create_server(**server_params)
#         if client_params is None:
#             client_params = {}
#         client = Client(aiohttp.ClientSession(loop=loop, **client_params), url)
#         return app, client
#
#     yield maker
#     client.close()
#
#
# @pytest.mark.tryfirst
# def pytest_pycollect_makeitem(collector, name, obj):
#     if collector.funcnamefilter(name):
#         if not callable(obj):
#             return
#         item = pytest.Function(name, parent=collector)
#         if 'run_loop' in item.keywords:
#             return list(collector._genfunctions(name, obj))
#
#
# @pytest.mark.tryfirst
# def pytest_pyfunc_call(pyfuncitem):
#     """
#     Run asyncio marked test functions in an event loop instead of a normal
#     function call.
#     """
#     if 'run_loop' in pyfuncitem.keywords:
#         funcargs = pyfuncitem.funcargs
#         loop = funcargs['loop']
#         testargs = {arg: funcargs[arg]
#                     for arg in pyfuncitem._fixtureinfo.argnames}
#         loop.run_until_complete(pyfuncitem.obj(**testargs))
#         return True
#
#
# def pytest_runtest_setup(item):
#     if 'run_loop' in item.keywords and 'loop' not in item.fixturenames:
#         # inject an event loop fixture for all async tests
#         item.fixturenames.append('loop')
#
#
# def pytest_ignore_collect(path, config):
#     if 'test_py35' in str(path):
#         if sys.version_info < (3, 5, 0):
#             return True
import pytest
from aiohttp import web

from solo.cli.util import parse_app_config
from solo import init_webapp


@pytest.fixture
def app_config():
    config = parse_app_config('./test_config.yml')  # TODO: move path to outer scope
    return config


@pytest.fixture
def web_client(loop, test_client, app_config):
    app_manager = loop.run_until_complete(init_webapp(loop, app_config))
    app = app_manager.app
    return loop.run_until_complete(test_client(app))
