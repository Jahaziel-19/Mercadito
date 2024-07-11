"""empty message

Revision ID: 6a7f6935d3f4
Revises: f8a307515e48
Create Date: 2024-07-10 22:31:55.840240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a7f6935d3f4'
down_revision = 'f8a307515e48'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.add_column(sa.Column('estatus', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.drop_column('estatus')

    # ### end Alembic commands ###
