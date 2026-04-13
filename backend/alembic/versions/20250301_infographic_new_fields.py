"""Rebuild infographic columns: drop template_type, add new infographic params.

Revision ID: 20250301_infographic_fields
Revises: 20250301_suggested_filename
Create Date: 2025-03-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250301_infographic_fields'
down_revision = '20250301_suggested_filename'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('infographics', 'template_type')
    op.drop_column('infographics', 'output_language')
    op.add_column(
        'infographics',
        sa.Column('suggested_filename', sa.String(255), nullable=True),
    )
    op.add_column(
        'infographics',
        sa.Column(
            'infographic_style',
            sa.String(100),
            nullable=False,
            server_default='标准',
        ),
    )
    op.add_column(
        'infographics',
        sa.Column(
            'infographic_language',
            sa.String(50),
            nullable=False,
            server_default='简体中文',
        ),
    )
    op.add_column(
        'infographics',
        sa.Column(
            'infographic_direction',
            sa.String(50),
            nullable=False,
            server_default='横向',
        ),
    )
    op.add_column(
        'infographics',
        sa.Column('infographic_custom_prompt', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('infographics', 'infographic_custom_prompt')
    op.drop_column('infographics', 'infographic_direction')
    op.drop_column('infographics', 'infographic_language')
    op.drop_column('infographics', 'infographic_style')
    op.drop_column('infographics', 'suggested_filename')
    op.add_column(
        'infographics',
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
            'template_type',
            sa.String(50),
            nullable=False,
            server_default='timeline',
        ),
    )
