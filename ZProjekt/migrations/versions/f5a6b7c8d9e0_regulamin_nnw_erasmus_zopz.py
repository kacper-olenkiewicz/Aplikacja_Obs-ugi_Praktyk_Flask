"""regulamin_nnw_erasmus_zopz

Revision ID: f5a6b7c8d9e0
Revises: e4f7c9b12a35
Create Date: 2026-04-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f5a6b7c8d9e0'
down_revision = 'e4f7c9b12a35'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('regulamin_zapoznany', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('ubezpieczenie_nnw', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('erasmus_plus', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('dziennik_potwierdzony_zopz', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('sprawozdanie_podpisane_zopz', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('sprawozdanie_podpisane_zopz')
        batch_op.drop_column('dziennik_potwierdzony_zopz')
        batch_op.drop_column('erasmus_plus')
        batch_op.drop_column('ubezpieczenie_nnw')
        batch_op.drop_column('regulamin_zapoznany')
