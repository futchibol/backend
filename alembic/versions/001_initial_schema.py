"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-08
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(3), nullable=False),
        sa.Column("flag_emoji", sa.String(), nullable=True),
        sa.Column("group_letter", sa.String(1), nullable=True),
        sa.Column("confederation", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "polla_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("invite_code", sa.String(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_polla_groups_id", "polla_groups", ["id"])
    op.create_index("ix_polla_groups_invite_code", "polla_groups", ["invite_code"], unique=True)

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_number", sa.Integer(), nullable=True),
        sa.Column("stage", sa.String(20), nullable=False),
        sa.Column("group_letter", sa.String(1), nullable=True),
        sa.Column("team1_id", sa.Integer(), nullable=True),
        sa.Column("team2_id", sa.Integer(), nullable=True),
        sa.Column("team1_placeholder", sa.String(), nullable=True),
        sa.Column("team2_placeholder", sa.String(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("venue", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("team1_score", sa.Integer(), nullable=True),
        sa.Column("team2_score", sa.Integer(), nullable=True),
        sa.Column("winner_id", sa.Integer(), nullable=True),
        sa.Column("went_to_extra_time", sa.Boolean(), nullable=True),
        sa.Column("went_to_penalties", sa.Boolean(), nullable=True),
        sa.Column("is_finished", sa.Boolean(), nullable=True),
        sa.Column("points_calculated", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["team1_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["team2_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["winner_id"], ["teams.id"]),
        sa.UniqueConstraint("match_number"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_matches_id", "matches", ["id"])

    op.create_table(
        "polla_group_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("total_points", sa.Integer(), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["polla_groups.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("group_id", "user_id"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("predicted_team1_score", sa.Integer(), nullable=True),
        sa.Column("predicted_team2_score", sa.Integer(), nullable=True),
        sa.Column("predicted_winner_id", sa.Integer(), nullable=True),
        sa.Column("points_earned", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["polla_groups.id"]),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.ForeignKeyConstraint(["predicted_winner_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "group_id", "match_id"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("predictions")
    op.drop_table("polla_group_members")
    op.drop_table("matches")
    op.drop_table("polla_groups")
    op.drop_table("teams")
    op.drop_table("users")
