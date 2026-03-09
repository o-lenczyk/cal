"""add meeting_date to users

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6g7h8i9j0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6g7h8i9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add meeting_date with default for existing rows (votes for 03.03.2026)
    op.add_column("users", sa.Column("meeting_date", sa.Date(), nullable=True))
    op.execute("UPDATE users SET meeting_date = '2026-03-03' WHERE meeting_date IS NULL")
    op.alter_column(
        "users",
        "meeting_date",
        existing_type=sa.Date(),
        nullable=False,
    )
    # Drop old unique on google_id, add (google_id, meeting_date)
    op.drop_constraint("uq_users_google_id", "users", type_="unique")
    op.create_unique_constraint("uq_user_google_meeting", "users", ["google_id", "meeting_date"])
    # Set next_meeting_date to 10.03.2026 so new votes go there (empty), old votes stay on 03.03
    op.execute(
        "INSERT INTO app_settings (key, value) VALUES ('next_meeting_date', '2026-03-10') "
        "ON CONFLICT (key) DO UPDATE SET value = '2026-03-10'"
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_google_meeting", "users", type_="unique")
    op.create_unique_constraint("uq_users_google_id", "users", ["google_id"])
    op.drop_column("users", "meeting_date")
