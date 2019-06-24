import logging
import pytest
import time
import socket

import psycopg2
import redis
from faker import Faker
from docker.api import APIClient as DockerAPIClient
from docker import from_env as docker_from_env
import webtest_asgi

import solo
from solo.config import docker_compose as compose_config
from solo.configurator import AIOManager
from . import TESTS_ROOT


@pytest.fixture(scope='session')
def testing_session_id():
    """ Something that we can use to identify the session,
    and is more readable than uuid.
    """
    fake = Faker()
    return fake.slug()


@pytest.fixture(scope='session')
def logger(app_config):
    logging.config.dictConfig(app_config.logging)
    return logging.getLogger('solo-tests')


@pytest.fixture(scope='session')
def app_config() -> solo.config.Config:
    # TODO: move path to outer scope
    cfg_path = TESTS_ROOT.parent / 'test_config.yml'
    config = solo.cli.parse_app_config(cfg_path)
    yield config


@pytest.fixture(scope='session')
def docker_compose_config() -> compose_config.Config:
    cfg_path = TESTS_ROOT.parent / 'env' / 'dev' / 'docker-compose.yml'
    config = solo.cli.parse_compose_config(cfg_path)
    yield config


@pytest.fixture(scope='session')
def docker_client() -> DockerAPIClient:
    return docker_from_env().api

@pytest.fixture
def solo_aio(
    loop,
    app_config,
    pg_server,
    redis_server,
) -> AIOManager:
    with solo.application_entrypoint(loop, app_config) as app_manager:
        yield app_manager


@pytest.fixture
def web_client(
    loop,
    solo_aio,
) -> webtest_asgi.TestClient:
    return webtest_asgi.TestClient(solo_aio.app)


@pytest.fixture(scope='session')
def unused_host_port():
    def port_selector():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

    return port_selector


@pytest.fixture(scope='session')
def pg_server(
    docker_client,
    app_config,
    docker_compose_config,
    testing_session_id,
    unused_host_port,
    logger,
):
    logger.info('Attempting to start Postgresql container')

    service = docker_compose_config.services.postgres

    if app_config.testing.docker_pull:
        image = service.image
        docker_client.pull(repository=image.name, tag=image.tag)

    pg_ports = service.ports
    container_args = dict(
        image=service.image.full_name,
        name=f'solo-pg-test-server-{testing_session_id}',
        ports=[
            p.host_port and f'{p.host_port}:{p.container_port}' or p.container_port
            for p in pg_ports
        ],
        environment=service.environment._asdict(),
        detach=True,
    )

    host = "127.0.0.1"
    host_port = pg_ports[0].host_port or unused_host_port()
    container_port = pg_ports[0].container_port
    port_bindings = {container_port: (host, host_port)}

    logger.info(f'Linking containerized Postgres on port {container_port} '
                f'to {host}:{host_port}')

    container_args['host_config'] = docker_client.create_host_config(
        port_bindings=port_bindings
    )

    container = docker_client.create_container(**container_args)

    try:
        docker_client.start(container=container['Id'])
        server_params = dict(
            database=service.environment.POSTGRES_DB,
            user=service.environment.POSTGRES_USER,
            password=service.environment.POSTGRES_PASSWORD,
            host=host,
            port=host_port
        )
        delay = 0.01
        for i in range(100):
            logger.info(f'Attempting to connect to the containerized Postgres {host_port}...')
            try:
                with psycopg2.connect(**server_params) as conn:
                    with conn.cursor() as cur:
                        cur.execute("CREATE EXTENSION intarray;")
                        break
            except psycopg2.Error:
                time.sleep(delay)
                delay *= 2
        else:
            pytest.fail(
                'Unable to initialize Postgresql from docker-compose'
            )

        container['host'] = host
        container['port'] = host_port
        container['pg_params'] = server_params

        yield container

    finally:
        docker_client.kill(container=container['Id'])
        docker_client.remove_container(container['Id'])


@pytest.fixture(scope='session')
def redis_server(
    docker_client,
    app_config,
    docker_compose_config,
    testing_session_id,
    unused_host_port,
    logger,
):
    logger.info('Attempting to start Redis container')

    service = docker_compose_config.services.redis

    if app_config.testing.docker_pull:
        image = service.image
        docker_client.pull(repository=image.name, tag=image.tag)

    redis_ports = service.ports
    container_args = dict(
        image=service.image.full_name,
        name=f'solo-redis-test-server-{testing_session_id}',
        ports=[
            p.host_port and f'{p.host_port}:{p.container_port}' or p.container_port
            for p in redis_ports
        ],
        detach=True,
    )

    host = "127.0.0.1"
    host_port = redis_ports[0].host_port or unused_host_port()
    container_port = redis_ports[0].container_port
    port_bindings = {container_port: (host, host_port)}

    logger.info(f'Linking containerized Redis on port {container_port} '
                f'to {host}:{host_port}')

    container_args['host_config'] = docker_client.create_host_config(
        port_bindings=port_bindings
    )

    container = docker_client.create_container(**container_args)

    try:
        docker_client.start(container=container['Id'])
        server_params = dict(
            host=host,
            port=host_port,
        )
        delay = 0.01
        for i in range(100):
            logger.info('Attempting to connect to the containerized Redis...')
            try:
                r = redis.Redis(**server_params)
                r.ping()
                break
            except redis.exceptions.ConnectionError:
                time.sleep(delay)
                delay *= 2
        else:
            pytest.fail(
                'Unable to initialize Redis from docker-compose'
            )

        container['host'] = host
        container['port'] = host_port
        container['redis_params'] = server_params

        yield container

    finally:
        docker_client.kill(container=container['Id'])
        docker_client.remove_container(container['Id'])
