"""trigger para updated_at nativo por columna

Revision ID: f9bf39894b8a
Revises: afd0ba8742a7
Create Date: 2025-12-22 20:48:32.269272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9bf39894b8a'
down_revision: Union[str, Sequence[str], None] = 'afd0ba8742a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION set_updated_at()
    RETURNS trigger AS $$
    BEGIN
      NEW.updated_at = now();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    DROP TRIGGER IF EXISTS trg_entity_mentions_updated_at ON entity_mentions;
    CREATE TRIGGER trg_entity_mentions_updated_at
    BEFORE UPDATE ON entity_mentions
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
    """)

def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_entity_mentions_updated_at ON entity_mentions;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
