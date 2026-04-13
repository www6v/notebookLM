"""Add source_count to studio tables (mind_maps, slide_decks, infographics, reports).

Revision ID: 20250315_source_count
Revises: 20250309_user_settings_theme
Create Date: 2025-03-15

"""
from alembic import op
import sqlalchemy as sa


revision = '20250315_source_count'
down_revision = '20250309_user_settings_theme'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'mind_maps',
        sa.Column('source_count', sa.Integer(), nullable=True),
    )
    op.add_column(
        'slide_decks',
        sa.Column('source_count', sa.Integer(), nullable=True),
    )
    op.add_column(
        'infographics',
        sa.Column('source_count', sa.Integer(), nullable=True),
    )
    op.add_column(
        'reports',
        sa.Column('source_count', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('reports', 'source_count')
    op.drop_column('infographics', 'source_count')
    op.drop_column('slide_decks', 'source_count')
    op.drop_column('mind_maps', 'source_count')
