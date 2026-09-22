"""add payment method

Revision ID: c4d7e2f1a9b3
Revises: f2a9c1d8e6b7
Create Date: 2026-09-22

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "c4d7e2f1a9b3"
down_revision: str | Sequence[str] | None = "f2a9c1d8e6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE paymentmethod AS ENUM ('CASH', 'CARD', 'BANK_TRANSFER')"
    )
    op.add_column(
        "payments",
        sa.Column(
            "method",
            sa.Enum("CASH", "CARD", "BANK_TRANSFER", name="paymentmethod"),
            nullable=False,
            server_default="CASH",
        ),
    )


def downgrade() -> None:
    op.drop_column("payments", "method")
    op.execute("DROP TYPE paymentmethod")
