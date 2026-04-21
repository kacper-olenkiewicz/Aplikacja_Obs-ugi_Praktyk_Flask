"""ocena_zopz_efekty

Revision ID: g6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-04-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'g6b7c8d9e0f1'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ocena_zopz_parametryczna', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocena_zopz_opisowa', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('efekty_potwierdzone_zopz', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('efekty_potwierdzone_zopz')
        batch_op.drop_column('ocena_zopz_opisowa')
        batch_op.drop_column('ocena_zopz_parametryczna')
