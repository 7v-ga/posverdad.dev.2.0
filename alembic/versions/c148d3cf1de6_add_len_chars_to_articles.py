"""add len_chars to articles

Revision ID: c148d3cf1de6
Revises: 49ae660fe36c
Create Date: 2025-12-22 16:02:15.659342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c148d3cf1de6'
down_revision: Union[str, Sequence[str], None] = '89e2efc59372'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("len_chars", sa.Integer(), nullable=False, server_default="0"),
    )

    # opcional: si quieres quitar el default de servidor para que quede “limpio”
    op.alter_column("articles", "len_chars", server_default=None)


def downgrade() -> None:
    op.drop_column("articles", "len_chars")
