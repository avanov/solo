import enum
import sqlalchemy as sa

from solo.server.model import Base
from solo.server.db.types import PythonMappedEnum
from solo.configurator.models import register_model


class AuthProvider(enum.Enum):
    EMAIL = 'email'
    GITHUB = 'github'



@register_model(category='users')
class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)


class Auth(Base):
    __tablename__ = 'auth'

    id = sa.Column(sa.BigInteger, primary_key=True)
    provider = sa.Column(PythonMappedEnum(AuthProvider), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)
    auth_key = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='', index=True)
