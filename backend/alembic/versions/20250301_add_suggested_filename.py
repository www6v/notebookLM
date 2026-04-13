"""Add suggested_filename to mind_maps and slide_decks tables.

Revision ID: 20250301_suggested_filename
Revises: 20250301_output_lang
Create Date: 2025-03-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250301_suggested_filename'
down_revision = '20250301_user_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'mind_maps',
        sa.Column('suggested_filename', sa.String(255), nullable=True),
    )
    op.add_column(
        'slide_decks',
        sa.Column('suggested_filename', sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('slide_decks', 'suggested_filename')
    op.drop_column('mind_maps', 'suggested_filename')
