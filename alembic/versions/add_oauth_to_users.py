"""add oauth fields to users

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_id", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_users_google_id", "users", ["google_id"])

    # Drop unique on name so multiple OAuth users can share the same display name
    op.drop_constraint("users_name_key", "users", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("users_name_key", "users", ["name"])
    op.drop_constraint("uq_users_google_id", "users", type_="unique")
    op.drop_column("users", "email")
    op.drop_column("users", "google_id")
