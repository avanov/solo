import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


metadata = sa.MetaData()

TraitsTbl = sa.Table('traits', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(140), nullable=False, index=True)
)

PeopleTbl = sa.Table('people', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(140), nullable=False, index=True),
    sa.Column('traits', ARRAY(sa.Integer, dimensions=1), nullable=False, server_default='{}')
)
