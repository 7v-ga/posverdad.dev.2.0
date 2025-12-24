# tests/integration/test_storage.py
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import psycopg
import pytest

from tests._db import db_url_for_psycopg, truncate_all, seed_minimal_fks
from scrapy_project.storage_helpers import save_entities

pytestmark = pytest.mark.integration


# ----------------------------
# DSN helpers
# ----------------------------
def _db_url() -> str:
    """
    Devuelve un DSN compatible con psycopg.
    - SQLAlchemy usa: postgresql+psycopg://...
    - psycopg usa:    postgresql://...
    """
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or ""
    if not url:
        user = os.getenv("POSTGRES_USER", "posverdad")
        pwd = os.getenv("POSTGRES_PASSWORD", "posverdad")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "posverdad")
        url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

    if url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    if url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://", 1)

    return url


# ----------------------------
# DB helpers
# ----------------------------
def _table_exists(cur, name: str) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
          SELECT 1
            FROM information_schema.tables
           WHERE table_schema='public'
             AND table_name=%s
        )
        """,
        (name,),
    )
    return bool(cur.fetchone()[0])


def _columns(cur, table: str) -> List[str]:
    cur.execute(
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_schema='public'
           AND table_name=%s
         ORDER BY ordinal_position
        """,
        (table,),
    )
    return [r[0] for r in cur.fetchall()]


def _truncate_all(cur) -> None:
    """
    Trunca tablas relevantes si existen.
    CASCADE para resetear FKs.
    """
    candidates = [
        "entity_actions",
        "entity_mentions",
        "articles_entities",
        "entities",
        "articles",
        "sources",
        "categories",
    ]
    existing = [t for t in candidates if _table_exists(cur, t)]
    if not existing:
        return
    cur.execute(f"TRUNCATE {', '.join(existing)} RESTART IDENTITY CASCADE")


def _seed_minimal_fks(cur) -> None:
    if _table_exists(cur, "sources"):
        cur.execute("INSERT INTO sources (id, name) VALUES (%s, %s)", (1, "Example Source"))
    if _table_exists(cur, "categories"):
        cur.execute("INSERT INTO categories (id, name) VALUES (%s, %s)", (1, "News"))


def _insert_minimal_article(cur, article_id: int = 1) -> None:
    cols = _columns(cur, "articles")
    must = {"id", "url", "title", "body"}
    missing = must - set(cols)
    assert not missing, f"articles no tiene columnas requeridas para test: {missing}"

    # Base mínima
    data: Dict[str, Any] = {
        "id": article_id,
        "url": f"https://example.com/a{article_id}",
        "title": "Test Article",
        "body": "cuerpo de prueba",
    }

    # Opcionales si existen
    if "source_id" in cols:
        data["source_id"] = 1
    if "category_id" in cols:
        data["category_id"] = 1
    if "published_at" in cols:
        data["published_at"] = "NOW()"
    if "scraped_at" in cols:
        data["scraped_at"] = "NOW()"

    # len_chars: si existe, lo seteamos. Si fuera NOT NULL sin default, esto evita errores.
    if "len_chars" in cols:
        data["len_chars"] = 123

    # preprocessed_data opcional
    if "preprocessed_data" in cols:
        data["preprocessed_data"] = None

    col_names: List[str] = []
    placeholders: List[str] = []
    params: List[Any] = []

    for k, v in data.items():
        col_names.append(k)
        if v == "NOW()":
            placeholders.append("NOW()")
        else:
            placeholders.append("%s")
            params.append(v)

    sql = f"INSERT INTO articles ({', '.join(col_names)}) VALUES ({', '.join(placeholders)})"
    cur.execute(sql, tuple(params))


def _label_to_type(raw_label: str) -> str:
    """
    Mapea labels crudas típicas (spaCy, etc.) a tipos del sistema.
    Ajusta si tu DB usa otro set.
    """
    lab = (raw_label or "").upper()
    if lab in ("PER", "PERSON"):
        return "PERSON"
    if lab in ("ORG",):
        return "ORG"
    if lab in ("LOC",):
        return "LOC"
    if lab in ("GPE",):
        return "GPE"
    if lab in ("EVENT",):
        return "EVENT"
    if lab in ("WORK_OF_ART",):
        return "WORK_OF_ART"
    if lab in ("PRODUCT",):
        return "PRODUCT"
    return "OTHER"


def _try_fetch_mentions(cur, article_id: int) -> Optional[List[Tuple[str, str]]]:
    if not _table_exists(cur, "entity_mentions"):
        return None

    em_cols = _columns(cur, "entity_mentions")

    text_col = next((c for c in ("raw_text", "entity_text", "text") if c in em_cols), None)
    label_col = next((c for c in ("raw_label", "label") if c in em_cols), None)

    if not (text_col and label_col and "article_id" in em_cols):
        return None

    cur.execute(
        f"""
        SELECT {text_col}, {label_col}
          FROM entity_mentions
         WHERE article_id = %s
         ORDER BY id
        """,
        (article_id,),
    )
    rows = cur.fetchall()
    return rows if rows else []


def _try_fetch_preprocessed_entities(cur, article_id: int) -> Optional[List[Dict[str, Any]]]:
    cols = _columns(cur, "articles")
    if "preprocessed_data" not in cols:
        return None

    cur.execute("SELECT preprocessed_data FROM articles WHERE id=%s", (article_id,))
    pre = cur.fetchone()[0]
    if pre is None:
        return []

    if isinstance(pre, str):
        pre_obj = json.loads(pre)
    else:
        pre_obj = pre

    if not isinstance(pre_obj, dict):
        return []

    ents = pre_obj.get("entities")
    if ents is None:
        return []
    if not isinstance(ents, list):
        return []
    return ents


def _try_fetch_normalized_entities(cur, article_id: int) -> Optional[List[Tuple[str, Optional[str]]]]:
    """
    Busca entidades normalizadas vía articles_entities -> entities.
    Devuelve lista de (name, type?) si existe columna type.
    """
    if not (_table_exists(cur, "articles_entities") and _table_exists(cur, "entities")):
        return None

    ae_cols = _columns(cur, "articles_entities")
    e_cols = _columns(cur, "entities")

    if not ("article_id" in ae_cols and "entity_id" in ae_cols):
        return None

    name_col = "name" if "name" in e_cols else None
    if not name_col:
        return None

    type_col = "type" if "type" in e_cols else None

    if type_col:
        cur.execute(
            f"""
            SELECT e.{name_col}, e.{type_col}
              FROM articles_entities ae
              JOIN entities e ON e.id = ae.entity_id
             WHERE ae.article_id = %s
             ORDER BY e.id
            """,
            (article_id,),
        )
    else:
        cur.execute(
            f"""
            SELECT e.{name_col}, NULL
              FROM articles_entities ae
              JOIN entities e ON e.id = ae.entity_id
             WHERE ae.article_id = %s
             ORDER BY e.id
            """,
            (article_id,),
        )

    rows = cur.fetchall()
    return rows if rows else []


# ----------------------------
# Tests
# ----------------------------
def test_save_entities_persists_somewhere_expected():
    """
    Este test valida que save_entities realmente persiste entidades
    en alguna de las rutas admitidas por el proyecto:
      1) entity_mentions (crudas), o
      2) articles.preprocessed_data.entities, o
      3) entities + articles_entities (normalizadas)

    Si no aparece en ninguna: el bug está en save_entities (no persiste).
    """
    entities = [
        {"text": "Estado", "label": "LOC"},
        {"text": "IPS", "label": "ORG"},
    ]

    with psycopg.connect(db_url_for_psycopg()) as conn:
        with conn.cursor() as cur:
            _truncate_all(cur)
            _seed_minimal_fks(cur)
            _insert_minimal_article(cur, article_id=1)

            save_entities(conn, 1, entities)

            # 1) menciones crudas
            mentions = _try_fetch_mentions(cur, 1)
            if mentions is not None and len(mentions) > 0:
                assert mentions == [("Estado", "LOC"), ("IPS", "ORG")]
                conn.commit()
                return

            # 2) preprocessed_data
            pre_ents = _try_fetch_preprocessed_entities(cur, 1)
            if pre_ents is not None and len(pre_ents) > 0:
                assert pre_ents == entities
                conn.commit()
                return

            # 3) normalizadas
            norm = _try_fetch_normalized_entities(cur, 1)
            if norm is not None and len(norm) > 0:
                names = [r[0] for r in norm]
                assert set(names) == {"Estado", "IPS"}

                # si hay type, lo validamos; si no, sólo nombres
                if norm[0][1] is not None:
                    got = {(n, t) for (n, t) in norm}
                    expected = {(e["text"], _label_to_type(e["label"])) for e in entities}
                    # Permitimos que el sistema haya normalizado a OTHER en algunos casos,
                    # pero al menos debería coincidir para ORG/LOC si tu pipeline lo setea.
                    assert any((n, t) in got for (n, t) in expected)

                conn.commit()
                return

            # Si llegamos aquí: no persistió en ningún lado
            raise AssertionError(
                "save_entities() no persistió entidades en entity_mentions, "
                "ni en articles.preprocessed_data.entities, "
                "ni en entities/articles_entities. Revisar implementación."
            )
