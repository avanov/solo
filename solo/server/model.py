import json
from typing import Iterable, Dict, Any, Set, Optional

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


class _BaseModel:
    FIELDS = tuple()
    IN_MODIFIERS = {}
    OUT_MODIFIERS = {
        'str': str,
        'json': json.dumps,
    }
    DEFAULT_MODIFIERS = {}

    #def __init__(self, **kwargs):
    #    for k, v in kwargs.items():
    #        setattr(self, k, v)

    def as_dict(self, *fields: Iterable[str], exclude: Optional[Set[str]] = None) -> Dict[str, Any]:
        if exclude is None:
            exclude = set()
        if not fields:
            fields = [k for k in self.__table__.c.keys() if k not in exclude]

        rv = {}
        out_modifiers = self.OUT_MODIFIERS
        for f in fields:
            field, *modifiers = f.split('|')
            field = field.strip()
            v = getattr(self, field)
            for m in modifiers:
                v = out_modifiers[m.strip()](v)
            rv[field] = v
        return rv


metadata = sa.MetaData()
Base = declarative_base(metadata=metadata, cls=_BaseModel)
