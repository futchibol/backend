"""add external_id to matches

Revision ID: 002
Revises: 001
Create Date: 2026-06-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("external_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_matches_external_id", "matches", ["external_id"])


def downgrade() -> None:
    op.drop_constraint("uq_matches_external_id", "matches", type_="unique")
    op.drop_column("matches", "external_id")
