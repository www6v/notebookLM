"""Add output_language to mind_maps and infographics tables.

Revision ID: 20250301_output_lang
Revises: 20250228_slide_opts
Create Date: 2025-03-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250301_output_lang'
down_revision = '20250228_slide_opts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'mind_maps',
        sa.Column(
            'output_language',
            sa.String(50),
            nullable=False,
            server_default='简体中文',
        ),
    )
    op.add_column(
        'infographics',
        sa.Column(
            'output_language',
            sa.String(50),
            nullable=False,
            server_default='简体中文',
        ),
    )


def downgrade() -> None:
    op.drop_column('infographics', 'output_language')
    op.drop_column('mind_maps', 'output_language')
