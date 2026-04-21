"""sprawozdanie_trzy_sekcje

Revision ID: j9e0f1a2b3c4
Revises: i8d9e0f1a2b3
Create Date: 2026-04-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'j9e0f1a2b3c4'
down_revision = 'i8d9e0f1a2b3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sprawozdanie_charakterystyka', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('sprawozdanie_opis_prac', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('sprawozdanie_samoocena', sa.Text(), nullable=True))

    # przeniesienie danych ze starych pol
    op.execute("UPDATE praktyki SET sprawozdanie_opis_prac = sprawozdanie_tresc WHERE sprawozdanie_tresc IS NOT NULL")
    op.execute("UPDATE praktyki SET sprawozdanie_samoocena = sprawozdanie_wnioski WHERE sprawozdanie_wnioski IS NOT NULL")

    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('sprawozdanie_tresc')
        batch_op.drop_column('sprawozdanie_wnioski')


def downgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sprawozdanie_tresc', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('sprawozdanie_wnioski', sa.Text(), nullable=True))

    op.execute("UPDATE praktyki SET sprawozdanie_tresc = sprawozdanie_opis_prac WHERE sprawozdanie_opis_prac IS NOT NULL")
    op.execute("UPDATE praktyki SET sprawozdanie_wnioski = sprawozdanie_samoocena WHERE sprawozdanie_samoocena IS NOT NULL")

    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('sprawozdanie_samoocena')
        batch_op.drop_column('sprawozdanie_opis_prac')
        batch_op.drop_column('sprawozdanie_charakterystyka')
