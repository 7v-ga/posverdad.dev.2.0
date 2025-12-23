"""defaults entity_mentions status decision_scope

Revision ID: 5678ba887dee
Revises: 4949cc122bd1
Create Date: 2025-12-22 20:35:31.342099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5678ba887dee'
down_revision: Union[str, Sequence[str], None] = '4949cc122bd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    # 1) defaults a nivel DB (server_default)
    op.alter_column(
        "entity_mentions",
        "status",
        existing_type=sa.Text(),
        nullable=False,
        server_default=sa.text("'raw'"),
    )
    op.alter_column(
        "entity_mentions",
        "decision_scope",
        existing_type=sa.Text(),
        nullable=False,
        server_default=sa.text("'article'"),
    )

    # 2) backfill explícito por si existieran filas antiguas con NULL
    op.execute("UPDATE entity_mentions SET status = 'raw' WHERE status IS NULL;")
    op.execute("UPDATE entity_mentions SET decision_scope = 'article' WHERE decision_scope IS NULL;")

    # 3) opcional: si quieres mantener el default permanentemente, no hagas nada.
    #    Si quieres obligar a que el código lo setee, quita el server_default:
    # op.alter_column("entity_mentions", "status", server_default=None)
    # op.alter_column("entity_mentions", "decision_scope", server_default=None)


def downgrade():
    # Si quitaste defaults en upgrade, aquí no hay mucho que hacer.
    # Si los mantuviste, los puedes remover:
    op.alter_column("entity_mentions", "decision_scope", server_default=None)
    op.alter_column("entity_mentions", "status", server_default=None)