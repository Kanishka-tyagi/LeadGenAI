"""add contact_email and scrape_data columns

Revision ID: 173dddc068bd
Revises: 70fb58e8e197
Create Date: 2026-08-09 13:04:46.638317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '173dddc068bd'
down_revision: Union[str, Sequence[str], None] = '70fb58e8e197'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
