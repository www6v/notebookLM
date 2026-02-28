"""Add slide_style, slide_language, slide_duration, slide_custom_prompt to slide_decks.

Revision ID: 20250228_slide_opts
Revises:
Create Date: 2025-02-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250228_slide_opts'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'slide_decks',
        sa.Column('slide_style', sa.String(100), nullable=False, server_default='detailed'),
    )
    op.add_column(
        'slide_decks',
        sa.Column('slide_language', sa.String(50), nullable=False, server_default='简体中文'),
    )
    op.add_column(
        'slide_decks',
        sa.Column('slide_duration', sa.String(50), nullable=False, server_default='default'),
    )
    op.add_column(
        'slide_decks',
        sa.Column('slide_custom_prompt', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('slide_decks', 'slide_custom_prompt')
    op.drop_column('slide_decks', 'slide_duration')
    op.drop_column('slide_decks', 'slide_language')
    op.drop_column('slide_decks', 'slide_style')
