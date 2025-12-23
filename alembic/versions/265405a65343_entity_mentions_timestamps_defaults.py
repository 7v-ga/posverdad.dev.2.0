"""entity_mentions timestamps defaults

Revision ID: 265405a65343
Revises: f9bf39894b8a
Create Date: 2025-12-22 20:56:06.647344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '265405a65343'
down_revision: Union[str, Sequence[str], None] = 'f9bf39894b8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # created_at / updated_at -> server_default NOW()
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
    op.alter_column(
        "entity_mentions",
        "created_at",
        server_default=None,
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )
    op.alter_column(
        "entity_mentions",
        "updated_at",
        server_default=None,
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )
