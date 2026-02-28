"""Add user_settings table.

Revision ID: 20250301_user_settings
Revises: 20250301_output_lang
Create Date: 2025-03-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250301_user_settings'
down_revision = '20250301_output_lang'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column(
            'user_id',
            sa.String(36),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column(
            'output_language',
            sa.String(50),
            nullable=False,
            server_default='简体中文',
        ),
        sa.Column(
            'llm_provider',
            sa.String(50),
            nullable=False,
            server_default='openai',
        ),
        sa.Column(
            'llm_model',
            sa.String(100),
            nullable=False,
            server_default='gpt-4o',
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('user_settings')
