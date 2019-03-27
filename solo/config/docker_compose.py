from typing import NamedTuple, Optional, Sequence

from typeit import type_constructor
from typeit.schema.primitives import Str


class _ContainerPortSchema(Str):
    def deserialize(self, node, cstruct):
        rv = super().deserialize(node, cstruct)
        if isinstance(rv, str):
            try:
                host_port, container_port = rv.split(':')
            except ValueError:
                container_port = rv
                host_port = None
            return ContainerPort(
                host_port=host_port,
                container_port=container_port
            )
        return rv


class _DockerImageSchema(Str):
    def deserialize(self, node, cstruct):
        rv = super().deserialize(node, cstruct)
        if isinstance(rv, str):
            try:
                name, tag = rv.split(':')
            except ValueError:
                name = rv
                tag = 'latest'
            return DockerImage(
                name=name,
                tag=tag
            )
        return rv


class ContainerPort(NamedTuple):
    host_port: Optional[str]
    container_port: str


class DockerImage(NamedTuple):
    name: str
    tag: str = 'latest'

    @property
    def full_name(self) -> str:
        return f'{self.name}:{self.tag}'


class ServicesRedis(NamedTuple):
    image: DockerImage
    ports: Sequence[ContainerPort]


class ServicesPostgresEnvironment(NamedTuple):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str


class ServicesPostgres(NamedTuple):
    image: DockerImage
    environment: ServicesPostgresEnvironment
    ports: Sequence[ContainerPort]


class Services(NamedTuple):
    postgres: ServicesPostgres
    redis: ServicesRedis


class Config(NamedTuple):
    version: str
    services: Services


mk_config, dict_config = (
    type_constructor & _ContainerPortSchema[ContainerPort]
                     & _DockerImageSchema[DockerImage]
                     ^ Config
)