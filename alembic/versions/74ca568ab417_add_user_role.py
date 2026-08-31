"""add user role

Revision ID: 74ca568ab417
Revises: 33e104407624
Create Date: 2026-08-31 17:47:01.496278

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "74ca568ab417"
down_revision: str | Sequence[str] | None = "33e104407624"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            server_default=sa.text("'member'"),
            nullable=False,
        ),
    )

    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('member', 'admin')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_users_role",
        "users",
        type_="check",
    )

    op.drop_column("users", "role")
