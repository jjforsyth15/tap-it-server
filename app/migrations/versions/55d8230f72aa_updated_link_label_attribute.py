"""Updated link label attribute

Revision ID: 55d8230f72aa
Revises: 0418146121a4
Create Date: 2026-06-09 21:41:04.627498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55d8230f72aa'
down_revision: Union[str, Sequence[str], None] = '0418146121a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
