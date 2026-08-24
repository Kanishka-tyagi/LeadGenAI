"""add job_id foreign key to leads

Revision ID: 60339323eee7
Revises: 173dddc068bd
Create Date: 2026-08-23 20:44:38.065014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60339323eee7'
down_revision: Union[str, Sequence[str], None] = '173dddc068bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
