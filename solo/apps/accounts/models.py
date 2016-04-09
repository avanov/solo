import sqlalchemy as sa

from solo.server.model import Base
from solo.configurator.models import register_model


@register_model(category='users')
class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.BigInteger, primary_key=True)
