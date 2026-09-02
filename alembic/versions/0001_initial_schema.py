"""initial schema: controls, evidence, score_snapshots

Matches the models as they stood at the end of Phase 5 (pre multi-user).
Enum columns store the Python enum *member names* (SQLAlchemy's default), e.g.
"ISO_27001_2022" / "NOT_STARTED" -- not the human-readable ``.value`` strings.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# create_type=False: the types are created/dropped explicitly below so that
# sharing one enum across two tables does not trigger a duplicate CREATE TYPE
# on PostgreSQL. On SQLite these render as VARCHAR and the explicit
# create/drop calls are skipped.
framework_enum = PGEnum(
    "ISO_27001_2022",
    "SOC_2",
    name="controlframework",
    create_type=False,
)
status_enum = PGEnum(
    "NOT_STARTED",
    "IN_PROGRESS",
    "IMPLEMENTED",
    "EVIDENCED",
    name="controlstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        framework_enum.create(bind, checkfirst=True)
        status_enum.create(bind, checkfirst=True)

    op.create_table(
        "controls",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("framework", framework_enum, nullable=False),
        sa.Column("theme", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("owner_note", sa.Text(), nullable=True),
        sa.Column("last_reviewed", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("control_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("file_path_or_url", sa.String(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("review_due", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["control_id"], ["controls.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "score_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("framework", framework_enum, nullable=False),
        sa.Column(
            "taken_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("theme_scores", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("score_snapshots")
    op.drop_table("evidence")
    op.drop_table("controls")
    if bind.dialect.name == "postgresql":
        status_enum.drop(bind, checkfirst=True)
        framework_enum.drop(bind, checkfirst=True)
