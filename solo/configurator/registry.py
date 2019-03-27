from typing import NamedTuple, Dict

from ..config.app import Config
from ..server.csrf import SessionCSRFStoragePolicy


class predvalseq(tuple):
    """ This class is a copy of ``pyramid.registry.predvalseq``

    A subtype of tuple used to represent a sequence of predicate values """
    pass


class Registry(NamedTuple):
    config: Config
    csrf_policy: SessionCSRFStoragePolicy
    settings: Dict = {}