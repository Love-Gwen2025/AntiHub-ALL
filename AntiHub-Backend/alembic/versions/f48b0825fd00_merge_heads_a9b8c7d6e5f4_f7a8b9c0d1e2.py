"""merge_heads_a9b8c7d6e5f4_f7a8b9c0d1e2

Revision ID: f48b0825fd00
Revises: a9b8c7d6e5f4, f7a8b9c0d1e2
Create Date: 2026-01-26

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f48b0825fd00"
down_revision: Union[str, Sequence[str], None] = ("a9b8c7d6e5f4", "f7a8b9c0d1e2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

