import sqlalchemy as sa

from solo.server.db.types import PythonMappedEnum
from solo.server.model import Base
from solo import SumType


class AuthProvider(SumType):
    GITHUB = 'github'


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