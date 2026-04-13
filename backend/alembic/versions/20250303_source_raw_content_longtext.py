"""Change sources.raw_content from TEXT to LONGTEXT to support large documents.

Revision ID: 20250303_raw_content_longtext
Revises: 20250301_infographic_fields
Create Date: 2025-03-03

"""
from alembic import op
from sqlalchemy.dialects.mysql import LONGTEXT


# revision identifiers, used by Alembic.
revision = '20250303_raw_content_longtext'
down_revision = '20250301_infographic_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'sources',
        'raw_content',
        type_=LONGTEXT,
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'sources',
        'raw_content',
        type_=LONGTEXT,
        existing_nullable=True,
    )
