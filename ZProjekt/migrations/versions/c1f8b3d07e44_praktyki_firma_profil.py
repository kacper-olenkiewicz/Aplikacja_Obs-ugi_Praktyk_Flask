"""praktyki_firma_profil

Revision ID: c1f8b3d07e44
Revises: b7d4a2e05c31
Create Date: 2026-04-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c1f8b3d07e44'
down_revision = 'b7d4a2e05c31'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('firma_profil', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('firma_profil')
