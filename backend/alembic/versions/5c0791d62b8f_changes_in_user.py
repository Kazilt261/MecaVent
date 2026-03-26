"""changes in user

Revision ID: 5c0791d62b8f
Revises: 00ba35bf1cdb
Create Date: 2026-03-07 18:30:36.038189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '5c0791d62b8f'
down_revision: Union[str, Sequence[str], None] = '00ba35bf1cdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
