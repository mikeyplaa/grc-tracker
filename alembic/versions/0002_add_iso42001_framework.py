"""add ISO 42001:2023 to the controlframework enum

Adds the ``ISO_42001_2023`` label to the PostgreSQL ``controlframework`` enum
type so ISO 42001 controls can be seeded. On SQLite the enum column is plain
VARCHAR with no constraint, so there is nothing to migrate there.

Revision ID: 0002_add_iso42001
Revises: 0001_initial
Create Date: 2026-09-02
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0002_add_iso42001"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block on older
    # PostgreSQL; autocommit_block is the supported Alembic idiom.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE controlframework ADD VALUE IF NOT EXISTS 'ISO_42001_2023'"
        )


def downgrade() -> None:
    # PostgreSQL cannot drop a single value from an enum type without recreating
    # it. Once the ISO 42001 controls are removed nothing references the label,
    # and leaving it in place is harmless -- so this is a deliberate no-op.
    pass
