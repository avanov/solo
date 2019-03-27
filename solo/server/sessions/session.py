from typing import NamedTuple, Any

from pyrsistent.typing import PMap


class Session(NamedTuple):
    data: PMap[str, Any]


async def update_session(sess: Session) -> Session:
    return sess
