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
