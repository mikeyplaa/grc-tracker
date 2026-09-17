"""add trust centre publishing flags to controls

Adds ``controls.is_public`` (default false) and ``controls.published_at``.
Existing rows stay unpublished, so turning the trust centre on never exposes
anything that was not explicitly published from the admin UI.

Revision ID: 0003_publishing
Revises: 0002_add_iso42001
Create Date: 2026-09-17
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_publishing"
down_revision: str | None = "0002_add_iso42001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default is required so the NOT NULL column can be added to a table
    # that already holds 174 seeded controls. sa.false() renders as `false` on
    # PostgreSQL and `0` on SQLite.
    with op.batch_alter_table("controls") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_public",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("published_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("controls") as batch_op:
        batch_op.drop_column("published_at")
        batch_op.drop_column("is_public")
