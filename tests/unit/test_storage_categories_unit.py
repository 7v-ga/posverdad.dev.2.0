import pytest
from unittest.mock import MagicMock
from scrapy_project.storage_helpers import (
    upsert_categories,
    link_article_categories,
    save_categories_and_link,
)

# ---------- upsert_categories: inserta/normaliza y retorna IDs ----------
def test_upsert_categories_inserts_and_normalizes():
    cur = MagicMock()
    # Simula fetchone() devolviendo IDs 1,2,3 en sucesivas llamadas
    cur.fetchone.side_effect = [(1,), (2,), (2,), (3,)]
    cats_in = [" Política ", "", "Economía", "Política", "Cultura"]
    ids = upsert_categories(cur, cats_in)
    assert ids == [1, 2, 2, 3]
    # Debe ejecutar INSERT...RETURNING por cada nombre no vacío/espaciado
    assert cur.execute.call_count == 4

# ---------- link_article_categories: crea N↔N evitando duplicados por ON CONFLICT ----------
def test_link_article_categories_executes_for_each_id():
    cur = MagicMock()
    link_article_categories(cur, article_id=99, category_ids=[1, 2, 2, 3])
    # Ejecuta 4 veces; el ON CONFLICT DO NOTHING evita duplicado a nivel DB
    assert cur.execute.call_count == 4

# ---------- save_categories_and_link: string/ lista; commit/rollback ----------
def test_save_categories_and_link_string_success_commits(monkeypatch):
    cur = MagicMock()
    # upsert -> ids 10, 20, 30
    cur.fetchone.side_effect = [(10,), (20,), (30,)]

    conn = MagicMock()
    conn.cursor.return_value = cur

    save_categories_and_link(conn, article_id=7, categories_value="Política, Economía , , Cultura")
    # 3 inserts en categories + 3 links en puente
    assert cur.execute.call_count == 6
    assert conn.commit.called

def test_save_categories_and_link_empty_input_returns_early():
    # No debe abrir cursor para entradas vacías/blancas
    conn = MagicMock()
    save_categories_and_link(conn, article_id=1, categories_value=" ,  , ")
    assert not conn.cursor.called

def test_save_categories_and_link_failure_rolls_back(monkeypatch):
    cur = MagicMock()
    cur.fetchone.side_effect = [(1,)]  # primera categoría OK

    conn = MagicMock()
    conn.cursor.return_value = cur

    # Forzamos que link_article_categories falle para ejercitar rollback
    import scrapy_project.storage_helpers as mod
    monkeypatch.setattr(mod, "link_article_categories", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fail")))

    with pytest.raises(RuntimeError):
        save_categories_and_link(conn, article_id=5, categories_value=["X"])

    assert conn.rollback.called
