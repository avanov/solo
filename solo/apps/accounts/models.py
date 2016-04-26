import sqlalchemy as sa

from solo.configurator.models import register_model
from solo.server.model import Base


@register_model(category='users')
class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(140), nullable=False, default='', server_default='')
