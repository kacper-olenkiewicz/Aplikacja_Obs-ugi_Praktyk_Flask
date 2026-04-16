"""praktyki_semestry_zaliczenie_sem6

Revision ID: a3c9e1f02b87
Revises: 4845f70310a6
Create Date: 2026-04-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3c9e1f02b87'
down_revision = '4845f70310a6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('semestr_od', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('semestr_do', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('zaliczenie_sem6', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('data_zaliczenia_sem6', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('komentarz_zaliczenia_sem6', sa.Text(), nullable=True))

    op.execute("UPDATE praktyki SET semestr_od = 6, semestr_do = 7 WHERE semestr_od IS NULL")


def downgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('komentarz_zaliczenia_sem6')
        batch_op.drop_column('data_zaliczenia_sem6')
        batch_op.drop_column('zaliczenie_sem6')
        batch_op.drop_column('semestr_do')
        batch_op.drop_column('semestr_od')
