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
    provider_uid = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='')
    """ Unique user identifier of a 3rd-party provider.
    """
    access_token = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='')
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)

    __table_args__ = (
        sa.UniqueConstraint('provider', 'provider_uid', name='uniq_provider_provider_uid'),
    )
