import logging
from typing import List, Optional

from aiohttp import web
from sqlalchemy import Table, Column, select
from sqlalchemy.orm.attributes import InstrumentedAttribute

from ..server.model import Base

log = logging.getLogger(__name__)


class SQLService:

    def __init__(self, app: web.Application, entity: Base, table: Optional[Table] = None):
        self.app = app
        self.engine = app.dbengine  # type: aiopg.sa.Engine
        if table is None:
            table = entity.__table__
        self.t = table
        self.e = entity

    async def get(self, search_field: InstrumentedAttribute,
                        search_value: str) -> Optional[Base]:
        rv = await self.get_many(search_field, [search_value], limit=1)
        if rv:
            return rv[0]
        return None

    async def get_many(self,
                       search_field: InstrumentedAttribute,
                       search_value: List[str],
                       limit: Optional[int] = None,
                       offset: int = 0) -> List[Base]:
        """ Return a collection of matched records up to the specified limit.
        """
        query = (select(self.columns())
                       .where(search_field.in_(search_value))
                       .offset(offset))
        if limit:
            query = query.limit(limit)
        async with self.engine.acquire() as c:
            csr = await c.execute(query)
            result = await csr.fetchall()
            entity = self.e
            return [entity(**record) for record in result]

    def columns(self, fields: Optional[List[str]] = None) -> List[InstrumentedAttribute]:
        """ Return columns to be used within select() statement constructors.
        """
        if not fields:
            fields = self.e.FIELDS
        entity = self.e
        return [getattr(entity, f) for f in fields]