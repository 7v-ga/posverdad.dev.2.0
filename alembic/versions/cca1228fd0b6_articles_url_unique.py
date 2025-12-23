"""articles url unique

Revision ID: cca1228fd0b6
Revises: c148d3cf1de6
Create Date: 2025-12-22 18:18:49.281506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cca1228fd0b6'
down_revision: Union[str, Sequence[str], None] = 'c148d3cf1de6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_articles_url", "articles", ["url"])

def downgrade() -> None:
    op.drop_constraint("uq_articles_url", "articles", type_="unique")
