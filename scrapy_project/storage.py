# scrapy_project/storage.py
from __future__ import annotations
from typing import Any, Tuple
import psycopg2
from psycopg2.extras import Json

def _is_cursor(db: Any) -> bool:
    # Cursor típico tiene .execute y .fetchone y no tiene .cursor()
    return hasattr(db, "execute") and hasattr(db, "fetchone") and not hasattr(db, "cursor")

def _as_cursor(db: Any) -> Tuple[Any, bool, bool]:
    """
    Devuelve (cursor, manage_tx, should_close)
    - Si db es cursor -> (db, False, False): no manejamos commit/rollback ni cerramos
    - Si db es conexión -> (db.cursor(), True, True): compat → commit/rollback y cerramos
    """
    if _is_cursor(db):
        return db, False, False
    cur = db.cursor()
    return cur, True, True

def _commit(db: Any, manage_tx: bool) -> None:
    if manage_tx and hasattr(db, "commit"):
        db.commit()

def _rollback(db: Any, manage_tx: bool) -> None:
    if manage_tx and hasattr(db, "rollback"):
        db.rollback()

def _close(cur: Any, should_close: bool) -> None:
    if should_close:
        try:
            cur.close()
        except Exception:
            pass

def save_preprocessed_data(article_id: int, preprocessed: dict, db: Any) -> None:
    """
    Actualiza el campo preprocessed_data del artículo.
    Acepta:
      - cursor (recomendado): NO realiza commit/rollback (parte de la transacción activa)
      - connection (compat): abre cursor, hace commit/rollback y cierra
    """
    cur, manage_tx, should_close = _as_cursor(db)
    try:
        cur.execute(
            "UPDATE articles SET preprocessed_data = %s WHERE id = %s;",
            (Json(preprocessed), article_id),
        )
        _commit(db, manage_tx)
    except Exception as e:
        _rollback(db, manage_tx)
        raise RuntimeError(f"❌ Error updating preprocessed_data for article {article_id}: {e}")
    finally:
        _close(cur, should_close)
