"""egzamin_wnioski_zaliczenia_przedluzenie

Revision ID: d2e5f8a14b06
Revises: c1f8b3d07e44
Create Date: 2026-04-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd2e5f8a14b06'
down_revision = 'c1f8b3d07e44'
branch_labels = None
depends_on = None


def upgrade():
    # data_do_przedluzenie na tabeli praktyki
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('data_do_przedluzenie', sa.Date(), nullable=True))

    # protokoly egzaminow
    op.create_table(
        'egzaminy_protokoly',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('praktyka_id', sa.Integer(), nullable=False),
        sa.Column('data_egzaminu', sa.Date(), nullable=False),
        sa.Column('przewodniczacy', sa.String(200), nullable=False),
        sa.Column('czlonkowie', sa.Text(), nullable=True),
        sa.Column('ocena', sa.String(20), nullable=False),
        sa.Column('uwagi', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['praktyka_id'], ['praktyki.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('praktyka_id'),
    )

    # wnioski o zaliczenie przez prace/staz/dzialalnosc
    op.create_table(
        'wnioski_zaliczenia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('typ', sa.String(30), nullable=False),
        sa.Column('pracodawca_nazwa', sa.String(255), nullable=False),
        sa.Column('pracodawca_adres', sa.String(255), nullable=True),
        sa.Column('nr_rejestrowy', sa.String(100), nullable=True),
        sa.Column('stanowisko', sa.String(200), nullable=True),
        sa.Column('data_od', sa.Date(), nullable=True),
        sa.Column('data_do', sa.Date(), nullable=True),
        sa.Column('opis_obowiazkow', sa.Text(), nullable=True),
        sa.Column('uzasadnienie', sa.Text(), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='zlozony'),
        sa.Column('ocena_komisji', sa.String(20), nullable=True),
        sa.Column('komentarz_komisji', sa.Text(), nullable=True),
        sa.Column('data_oceny_komisji', sa.Date(), nullable=True),
        sa.Column('decyzja_dyrektora', sa.String(20), nullable=True),
        sa.Column('komentarz_dyrektora', sa.Text(), nullable=True),
        sa.Column('data_decyzji', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # dokumenty do wniosku
    op.create_table(
        'wnioski_dokumenty',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wniosek_id', sa.Integer(), nullable=False),
        sa.Column('typ', sa.String(30), nullable=False),
        sa.Column('nazwa_oryginalna', sa.String(255), nullable=False),
        sa.Column('nazwa_pliku', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('rozmiar', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['wniosek_id'], ['wnioski_zaliczenia.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # wnioski o przedluzenie
    op.create_table(
        'wnioski_przedluzenia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('praktyka_id', sa.Integer(), nullable=False),
        sa.Column('powod', sa.String(30), nullable=False),
        sa.Column('godziny_nieobecnosci', sa.Integer(), nullable=True),
        sa.Column('opis', sa.Text(), nullable=True),
        sa.Column('proponowana_data_do', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='zlozony'),
        sa.Column('nowa_data_do', sa.Date(), nullable=True),
        sa.Column('komentarz', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['praktyka_id'], ['praktyki.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('wnioski_przedluzenia')
    op.drop_table('wnioski_dokumenty')
    op.drop_table('wnioski_zaliczenia')
    op.drop_table('egzaminy_protokoly')
    with op.batch_alter_table('praktyki', schema=None) as batch_op:
        batch_op.drop_column('data_do_przedluzenie')
