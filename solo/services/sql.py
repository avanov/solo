import logging
from typing import List, Iterable, Set, Optional

from sqlalchemy import Table, select
from sqlalchemy.orm.attributes import InstrumentedAttribute

from ..server.db.types import SQLEngine
from ..server.model import Base

log = logging.getLogger(__name__)


class SQLService:

    def __init__(self, db: SQLEngine, entity: Base, table: Optional[Table] = None):
        self.engine = db
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

    async def save(self, instance: Base) -> Base:
        columns = instance.__table__.c
        values = instance.as_dict(exclude={'id'})
        if instance.id is None:
            query = self.t.insert().values(**values).returning(columns.id)
        else:
            query = self.t.update().values(**values).where(columns.id == instance.id).returning(columns.id)
        async with self.engine.acquire() as c:
            csr = await c.execute(query)
            instance_id = await csr.scalar()
            instance.id = instance_id
            return instance

    def columns(self,
                fields: Optional[List[InstrumentedAttribute]] = None,
                exclude: Optional[Set[InstrumentedAttribute]] = None,
                entity: Optional[Base] = None) -> Iterable[InstrumentedAttribute]:
        """ Return columns to be used within select() statement constructors.
        """
        if entity is None:
            entity = self.e
        if exclude is None:
            exclude = set()
        if not fields:
            return (getattr(entity, f) for f in entity.__table__.c.keys() if getattr(entity, f) not in exclude)
        return (f for f in fields if f not in exclude)
