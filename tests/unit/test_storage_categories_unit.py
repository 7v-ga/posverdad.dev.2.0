# tests/unit/test_storage_categories_unit.py
import pytest
from unittest.mock import MagicMock
from scrapy_project.storage_helpers import (
    upsert_categories,
    link_article_categories,
    save_categories_and_link,
)

def _sql_startswith(call, prefix: str) -> bool:
    if not call.args:
        return False
    sql = str(call.args[0]).strip().lower()
    return sql.startswith(prefix.strip().lower())

def _filter_execute_calls(cur: MagicMock, prefix: str):
    return [c for c in cur.execute.call_args_list if _sql_startswith(c, prefix)]


# ---------- upsert_categories: inserta/normaliza y retorna IDs ----------
def test_upsert_categories_inserts_and_normalizes():
    cur = MagicMock()
    # Simula fetchone() devolviendo IDs 1,2,2,3 para 4 inputs válidos
    cur.fetchone.side_effect = [(1,), (2,), (2,), (3,)]

    cats_in = [" Política ", "", "Economía", "Política", "Cultura"]
    ids = upsert_categories(cur, cats_in)

    assert ids == [1, 2, 2, 3]

    # inputs no vacíos => 4 intentos de insert
    ins_calls = _filter_execute_calls(cur, "insert into categories")
    assert len(ins_calls) == 4


# ---------- link_article_categories: crea N↔N deduplicando a nivel app ----------
def test_link_article_categories_inserts_unique_pairs():
    cur = MagicMock()

    link_article_categories(cur, article_id=99, category_ids=[1, 2, 2, 3])

    # Medimos solo INSERTs al puente, ignorando checks auxiliares (to_regclass, etc.)
    link_calls = _filter_execute_calls(cur, "insert into articles_categories")

    # Contrato: dedup a nivel app (menos IO); duplicados se eliminan antes de ejecutar SQL
    assert len(link_calls) == 3

    params = [c.args[1] for c in link_calls]  # (article_id, category_id)
    assert set(params) == {(99, 1), (99, 2), (99, 3)}


# ---------- save_categories_and_link: string/ lista; commit/rollback ----------
def test_save_categories_and_link_string_success_commits():
    cur = MagicMock()
    cur.fetchone.side_effect = [(10,), (20,), (30,)]

    conn = MagicMock()
    conn.cursor.return_value = cur

    save_categories_and_link(conn, article_id=7, categories_value="Política, Economía , , Cultura")

    # 3 inserts categories + 3 inserts puente
    ins_cat = _filter_execute_calls(cur, "insert into categories")
    ins_link = _filter_execute_calls(cur, "insert into articles_categories")
    assert len(ins_cat) == 3
    assert len(ins_link) == 3
    assert conn.commit.called


def test_save_categories_and_link_empty_input_returns_early():
    conn = MagicMock()
    save_categories_and_link(conn, article_id=1, categories_value=" ,  , ")
    assert not conn.cursor.called


def test_save_categories_and_link_failure_rolls_back(monkeypatch):
    cur = MagicMock()
    cur.fetchone.side_effect = [(1,)]  # primera categoría OK

    conn = MagicMock()
    conn.cursor.return_value = cur

    import scrapy_project.storage_helpers as mod
    monkeypatch.setattr(
        mod,
        "link_article_categories",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")),
    )

    with pytest.raises(RuntimeError):
        save_categories_and_link(conn, article_id=5, categories_value=["X"])

    assert conn.rollback.called
