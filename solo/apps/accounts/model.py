from typing import TypeVar, Set
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

from solo import SumType
from solo.configurator.models import register_model
from solo.server.model import Base
from solo.server.db.types import PythonMappedEnum


class AuthProvider(SumType):
    GITHUB = 'github'
    FACEBOOK = 'facebook'


class Guest:
    id = 0
    name = 'Guest'
    _permissions = set()


@register_model(category='users')
class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='')


@register_model(category='auth')
class Auth(Base):
    __tablename__ = 'auth'

    id = sa.Column(sa.BigInteger, primary_key=True)
    provider = sa.Column(PythonMappedEnum(AuthProvider), nullable=False)
    provider_uid = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='')
    """ Unique user identifier of a 3rd-party provider.
    """
    access_token = sa.Column(sa.Unicode(200), nullable=False, default='', server_default='')
    user_id = sa.Column(User.__table__.c.id.type, sa.ForeignKey(User.__table__.c.id), nullable=False, index=True)

    __table_args__ = (
        sa.UniqueConstraint('provider', 'provider_uid', name='uniq_provider_provider_uid'),
    )


@register_model(category='users')
class Group(Base):
    __tablename__ = 'groups'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='')
    description = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='')
    permissions = sa.Column(JSON, nullable=False, default=list, server_default='[]')


users_groups_association = sa.Table('users_groups', Base.metadata,
    sa.Column('user_id', User.__table__.c.id.type, sa.ForeignKey(User.__table__.c.id, ondelete='CASCADE')),
    sa.Column('group_id', Group.__table__.c.id.type, sa.ForeignKey(Group.__table__.c.id, ondelete='CASCADE')),
    sa.PrimaryKeyConstraint('user_id', 'group_id')
)


UserType = TypeVar('UserType', User, Guest)


class Permissions:
    __slots__ = ('user', 'permissions')

    def __init__(self, user: UserType, permissions: Set[str]):
        self.user = user
        self.permissions = permissions

    def allowed(self, permission: str) -> bool:
        return permission in self.permissions
