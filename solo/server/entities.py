import json
from typing import Optional, Dict, Any, Iterable


class BaseEntity:
    FIELDS = tuple()
    IN_MODIFIERS = {}
    OUT_MODIFIERS = {
        'str': str,
        'json': json.dumps,
    }
    DEFAULT_MODIFIERS = {}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self, *fields: Iterable[str]) -> Dict[str, Any]:
        if not fields:
            fields = self.FIELDS

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
