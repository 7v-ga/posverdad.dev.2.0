"""entity_mentions timestamps defaults

Revision ID: afd0ba8742a7
Revises: 5678ba887dee
Create Date: 2025-12-22 20:44:12.346455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afd0ba8742a7'
down_revision: Union[str, Sequence[str], None] = '5678ba887dee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.alter_column(
        "entity_mentions",
        "created_at",
        server_default=sa.text("now()"),
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )
    op.alter_column(
        "entity_mentions",
        "updated_at",
        server_default=sa.text("now()"),
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )

def downgrade():
    op.alter_column("entity_mentions", "created_at", server_default=None)
    op.alter_column("entity_mentions", "updated_at", server_default=None)
