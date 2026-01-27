"""add_zai_image_accounts_table

Revision ID: c2d5e7f9a1b3
Revises: f48b0825fd00
Create Date: 2026-01-27

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d5e7f9a1b3"
down_revision: Union[str, None] = "f48b0825fd00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "zai_image_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("account_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.Integer(), server_default="1", nullable=False),
        sa.Column("credentials", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_zai_image_accounts_user_id"),
        "zai_image_accounts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_zai_image_accounts_status"),
        "zai_image_accounts",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_zai_image_accounts_status"), table_name="zai_image_accounts")
    op.drop_index(op.f("ix_zai_image_accounts_user_id"), table_name="zai_image_accounts")
    op.drop_table("zai_image_accounts")

