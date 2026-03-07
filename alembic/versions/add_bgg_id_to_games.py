"""add bgg_id to games

Revision ID: a1b2c3d4e5f6
Revises: 89b6d878dbed
Create Date: 2026-03-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "89b6d878dbed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games", sa.Column("bgg_id", sa.Integer(), nullable=True))
    op.create_index("ix_games_bgg_id", "games", ["bgg_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_games_bgg_id", table_name="games")
    op.drop_column("games", "bgg_id")
