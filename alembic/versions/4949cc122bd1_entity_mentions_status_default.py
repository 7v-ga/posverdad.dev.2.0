"""entity_mentions status default

Revision ID: 4949cc122bd1
Revises: cca1228fd0b6
Create Date: 2025-12-22 20:16:54.382522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4949cc122bd1'
down_revision: Union[str, Sequence[str], None] = 'cca1228fd0b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "entity_mentions",
        "status",
        server_default=sa.text("'raw'"),
        existing_type=sa.Text(),
        existing_nullable=False,
    )
