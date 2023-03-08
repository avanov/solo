import asyncio
from typing import Callable, Mapping, Any, get_type_hints, NamedTuple, Type, TypeVar, Awaitable, Tuple

from pyrsistent import pmap

from solo.configurator.registry import Registry
from solo.server.db.types import SQLEngine
from solo.server.request import Request
from solo.types import IO
from solo.vendor.old_session.old_session import Session, SessionStore


class Runtime(NamedTuple):
    registry: Registry
    dbengine: SQLEngine
    memstore: Any
    session_storage: SessionStore


def get_handler_deps(
    runtime: Runtime,
    handler: Callable,
    request: Request,
) -> Tuple[Mapping[str, IO], Mapping[str, Any]]:
    """ Returns a tuple of awaitable coroutine dependencies and rest dependencies.
    """
    hints = get_type_hints(handler)
    hints.pop('return', None)
    iter_hints = (x for x in hints.items() if x[0] != 'return')
    rv = {True: {}, False:{}}
    for arg_name, dep_type in iter_hints:
        dependency_getter = DEPENDENCIES[dep_type]
        dep = dependency_getter(runtime)
        if callable(dep):
            dep = dep(request)
        rv[asyncio.iscoroutine(dep)][arg_name] = dep
    return pmap(rv[True]), pmap(rv[False])


T = TypeVar('T')

DEPENDENCIES: Mapping[Type[T], Callable[[Runtime], T]] = pmap({
    Registry: lambda runtime: runtime.registry,
    SQLEngine: lambda runtime: runtime.db_engine,
    Session: lambda runtime: lambda request: runtime.session_storage.load_session(request),
    SessionStore: lambda runtime: runtime.session_storage,
})
