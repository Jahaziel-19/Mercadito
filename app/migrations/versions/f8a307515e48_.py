"""empty message

Revision ID: f8a307515e48
Revises: 1124b280e25d
Create Date: 2024-07-09 22:44:16.458895

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8a307515e48'
down_revision = '1124b280e25d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('alumno',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('nombre', sa.String(length=150), nullable=False),
    sa.Column('apellido_paterno', sa.String(length=150), nullable=False),
    sa.Column('apellido_materno', sa.String(length=150), nullable=False),
    sa.Column('carrera', sa.String(), nullable=True),
    sa.Column('foto_perfil', sa.String(length=255), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('rol', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('id')
    )
    op.drop_table('user')
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id_alumno', sa.String(), nullable=False))
        batch_op.drop_column('id_user')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pedido', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id_user', sa.VARCHAR(), nullable=False))
        batch_op.drop_column('id_alumno')

    op.create_table('user',
    sa.Column('id', sa.VARCHAR(), nullable=False),
    sa.Column('nombre', sa.VARCHAR(length=150), nullable=False),
    sa.Column('carrera', sa.VARCHAR(), nullable=True),
    sa.Column('foto_perfil', sa.VARCHAR(length=255), nullable=True),
    sa.Column('rol', sa.VARCHAR(length=255), nullable=False),
    sa.Column('password_hash', sa.VARCHAR(length=255), nullable=False),
    sa.Column('email', sa.VARCHAR(length=255), nullable=False),
    sa.Column('apellido_paterno', sa.VARCHAR(length=150), nullable=False),
    sa.Column('apellido_materno', sa.VARCHAR(length=150), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('id')
    )
    op.drop_table('alumno')
    # ### end Alembic commands ###
