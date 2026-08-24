"""add maps_data column to leads

Revision ID: a438a9614e2f
Revises: 60339323eee7
Create Date: 2026-08-24 10:16:02.197730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a438a9614e2f'
down_revision: Union[str, Sequence[str], None] = '60339323eee7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
