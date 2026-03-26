"""new var admin

Revision ID: 397a21632691
Revises: 5c0791d62b8f
Create Date: 2026-03-07 18:34:40.992842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '397a21632691'
down_revision: Union[str, Sequence[str], None] = '5c0791d62b8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
