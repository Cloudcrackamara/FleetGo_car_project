"""add damage payment kind

Revision ID: f2a9c1d8e6b7
Revises: eddf6d24e70f
Create Date: 2026-09-22

"""
from collections.abc import Sequence

from alembic import op


revision: str = "f2a9c1d8e6b7"
down_revision: str | Sequence[str] | None = "eddf6d24e70f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE paymentkind ADD VALUE IF NOT EXISTS 'DAMAGE'")


def downgrade() -> None:
    # PostgreSQL does not support removing an enum value in place.
    pass
