import sqlalchemy as sa

from solo import SumType
from solo.server.model import Base
from solo.server.db.types import PythonMappedEnum
from solo.configurator.models import register_model


class AuthProvider(SumType):
    EMAIL = 'email'
    GITHUB = 'github'
    FACEBOOK = 'facebook'


@register_model(category='users')
class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='')


class Auth(Base):
    __tablename__ = 'auth'

    id = sa.Column(sa.BigInteger, primary_key=True)
    provider = sa.Column(PythonMappedEnum(AuthProvider), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)
    auth_key = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='', index=True)
    """ Authentication key
    """

    __table_args__ = (
        sa.UniqueConstraint('provider', 'user_id', name='uniq_provider_user_id'),
        sa.UniqueConstraint('provider', 'auth_key', name='uniq_provider_auth_key')
    )
