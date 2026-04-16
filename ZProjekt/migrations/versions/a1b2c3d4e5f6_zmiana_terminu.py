"""Dodaje tabelę wnioski_zmiana_terminu (§3 Org. pkt 3 & 7)

Revision ID: a1b2c3d4e5f6
Revises: f5a6b7c8d9e0
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f5a6b7c8d9e0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'wnioski_zmiana_terminu',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('powod', sa.String(length=20), nullable=False),
        sa.Column('opis', sa.Text(), nullable=False),
        sa.Column('proponowany_semestr', sa.Integer(), nullable=True),
        sa.Column('proponowana_data_od', sa.Date(), nullable=True),
        sa.Column('proponowana_data_do', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='zlozony'),
        sa.Column('komentarz_dyrektora', sa.Text(), nullable=True),
        sa.Column('data_decyzji', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_wnioski_zmiana_terminu_student_id',
                    'wnioski_zmiana_terminu', ['student_id'])


def downgrade():
    op.drop_index('ix_wnioski_zmiana_terminu_student_id',
                  table_name='wnioski_zmiana_terminu')
    op.drop_table('wnioski_zmiana_terminu')
