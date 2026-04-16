"""praktyki_tryb_harmonogram_bhp

Revision ID: b7d4a2e05c31
Revises: a3c9e1f02b87
Create Date: 2026-04-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b7d4a2e05c31'
down_revision = 'a3c9e1f02b87'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tryb_realizacji', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('harmonogram', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('bhp_zaakceptowane', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('bhp_zaakceptowane')
        batch_op.drop_column('harmonogram')
        batch_op.drop_column('tryb_realizacji')
