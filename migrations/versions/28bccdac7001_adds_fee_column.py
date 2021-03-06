"""Adds fee column

Revision ID: 28bccdac7001
Revises: 3460331ee9a9
Create Date: 2014-04-16 17:34:26.936156

"""

# revision identifiers, used by Alembic.
revision = '28bccdac7001'
down_revision = '3460331ee9a9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pool', sa.Column('fee', sa.Float(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pool', 'fee')
    ### end Alembic commands ###
