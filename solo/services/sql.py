import logging
from typing import List, Optional

from aiohttp import web
from sqlalchemy import Table, Column, select

from ..server.entities import BaseEntity


log = logging.getLogger(__name__)


class SQLService:

    def __init__(self, app: web.Application, table: Table, entity: BaseEntity):
        self.app = app
        self.engine = app.dbengine  # type: aiopg.sa.Engine
        self.t = table
        self.e = entity

    async def get_many(self,
                       search_field: Column,
                       search_value: List[str],
                       limit: Optional[int] = None,
                       offset: int = 0) -> List[BaseEntity]:
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

    def columns(self, fields: Optional[List[str]] = None) -> List[Column]:
        """ Return columns to be used within select() statement constructors.
        """
        if not fields:
            fields = self.e.FIELDS
        columns = self.t.c
        return [getattr(columns, f) for f in fields]
