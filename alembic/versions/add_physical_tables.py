"""add physical tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create physical tables
    op.create_table(
        "tables",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Insert default tables: 2x6, 2x4
    op.execute("""
        INSERT INTO tables (name, capacity, sort_order) VALUES
        ('Table 1', 6, 1),
        ('Table 2', 6, 2),
        ('Table 3', 4, 3),
        ('Table 4', 4, 4)
    """)

    # Add table_id to table_instances (nullable first for migration)
    op.add_column("table_instances", sa.Column("table_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_table_instances_table_id",
        "table_instances",
        "tables",
        ["table_id"],
        ["id"],
    )

    # Migrate existing data: each table_instance needs its own physical table (unique constraint)
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id FROM table_instances ORDER BY id"))
    rows = result.fetchall()
    table_ids = [r[0] for r in conn.execute(sa.text("SELECT id FROM tables ORDER BY sort_order")).fetchall()]

    # Create more physical tables if we have more table_instances than tables
    for i in range(len(rows) - len(table_ids)):
        max_order = conn.execute(sa.text("SELECT COALESCE(MAX(sort_order), 0) FROM tables")).scalar()
        n = len(table_ids) + i + 1
        conn.execute(sa.text("INSERT INTO tables (name, capacity, sort_order) VALUES (:name, 6, :o)"), {"name": f"Table {n}", "o": max_order + 1})
        new_tid = conn.execute(sa.text("SELECT id FROM tables ORDER BY id DESC LIMIT 1")).scalar()
        table_ids.append(new_tid)

    for i, (ti_id,) in enumerate(rows):
        if i < len(table_ids):
            conn.execute(sa.text("UPDATE table_instances SET table_id = :tid WHERE id = :tiid"), {"tid": table_ids[i], "tiid": ti_id})

    op.alter_column(
        "table_instances",
        "table_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # Drop old columns and constraints
    op.drop_constraint("uq_game_table_number", "table_instances", type_="unique")
    op.drop_column("table_instances", "table_number")

    # Add new unique constraint (one game per physical table)
    op.create_unique_constraint("uq_table_instance_table_id", "table_instances", ["table_id"])


def downgrade() -> None:
    op.drop_constraint("uq_table_instance_table_id", "table_instances", type_="unique")
    op.add_column("table_instances", sa.Column("table_number", sa.Integer(), nullable=True))
    op.execute("UPDATE table_instances SET table_number = 1")
    op.alter_column("table_instances", "table_number", nullable=False)
    op.drop_constraint("fk_table_instances_table_id", "table_instances", type_="foreignkey")
    op.drop_column("table_instances", "table_id")
    op.create_unique_constraint("uq_game_table_number", "table_instances", ["game_id", "table_number"])
    op.drop_table("tables")
