"""users use uuid pk

Revision ID: 92c4c678030a
Revises: 6f74bc194fc0
Create Date: 2026-02-19 10:56:29.021270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '92c4c678030a'
down_revision: Union[str, Sequence[str], None] = '6f74bc194fc0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("users")
    
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email")
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("users")
    
    op.create_table(
        "users",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("email", sa.VARCHAR(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email")
    )
    # ### end Alembic commands ###
