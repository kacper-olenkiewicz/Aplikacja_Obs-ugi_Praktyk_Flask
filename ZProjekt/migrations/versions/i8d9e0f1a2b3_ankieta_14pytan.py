"""ankieta_14pytan

Revision ID: i8d9e0f1a2b3
Revises: h7c8d9e0f1a2
Create Date: 2026-04-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'i8d9e0f1a2b3'
down_revision = 'h7c8d9e0f1a2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        # usun stare pola
        batch_op.drop_column('ankieta_atmosfera')
        batch_op.drop_column('ankieta_organizacja')
        batch_op.drop_column('ankieta_wiedza')
        batch_op.drop_column('ankieta_komentarz')
        # dodaj 14 pytan + uwagi + metryczka
        for i in range(1, 15):
            batch_op.add_column(sa.Column(f'ankieta_p{i:02d}', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ankieta_uwagi', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('ankieta_rok_akademicki', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('ankieta_forma_studiow', sa.String(20), nullable=True))


def downgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('ankieta_forma_studiow')
        batch_op.drop_column('ankieta_rok_akademicki')
        batch_op.drop_column('ankieta_uwagi')
        for i in range(14, 0, -1):
            batch_op.drop_column(f'ankieta_p{i:02d}')
        batch_op.add_column(sa.Column('ankieta_komentarz', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('ankieta_wiedza', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ankieta_organizacja', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ankieta_atmosfera', sa.Integer(), nullable=True))
