"""hospitacje_zopz_porozumienie

Revision ID: e4f7c9b12a35
Revises: d2e5f8a14b06
Create Date: 2026-04-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e4f7c9b12a35'
down_revision = 'd2e5f8a14b06'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('opiekun_zakladowy_wyksztalcenie', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('porozumienie_podpisane', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('skierowanie_wystawione', sa.Boolean(), nullable=False, server_default='false'))

    op.create_table(
        'hospitacje',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('praktyka_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('prowadzacy', sa.String(200), nullable=False),
        sa.Column('notatka', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['praktyka_id'], ['praktyki.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('hospitacje')
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('skierowanie_wystawione')
        batch_op.drop_column('porozumienie_podpisane')
        batch_op.drop_column('opiekun_zakladowy_wyksztalcenie')
