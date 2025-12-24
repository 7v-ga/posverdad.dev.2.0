#!/usr/bin/env python3
"""
scripts/notify_summary.py

Resumen del último scraping y notificación a Slack.

Este archivo fue adaptado para la base nueva gestionada por Alembic y psycopg3:
- Ya NO depende de la tabla `nlp_runs` ni de la vista `v_run_summary`.
- Construye el resumen a partir de las tablas actuales:
  articles, sources, entities, entity_mentions (si existe y tiene datos).

Compatibilidad:
- Si `articles` tiene columna `run_id`, filtra por run_id cuando se entrega --run-id.
- Si NO existe `run_id`, usa una ventana temporal (por defecto últimas 24h) o el último día con datos.
"""

from __future__ import annotations

import os
import time
import json
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Tuple, List, Dict

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Row

# Opcional: gráficos
try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None  # type: ignore


# =========================
# Config
# =========================

SLACK_TOKEN = os.getenv("SLACK_TOKEN", "").strip()
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "").strip()
VERBOSE = os.getenv("VERBOSE", "0").strip() in ("1", "true", "True", "yes", "YES")

# Ventana fallback cuando no hay run_id (en horas)
DEFAULT_WINDOW_HOURS = int(os.getenv("SUMMARY_WINDOW_HOURS", "24"))


def db_url() -> str:
    """
    Prioridad:
    - DATABASE_URL
    - POSTGRES_URL
    """
    url = (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL/POSTGRES_URL no está configurado.")
    return url


def make_engine() -> Engine:
    return create_engine(db_url(), pool_pre_ping=True, future=True)


# =========================
# Slack helpers
# =========================

SLACK_API_BASE = "https://slack.com/api"


def slack_api(method: str, *, json_payload: Optional[dict] = None, data: Optional[dict] = None, files: Optional[dict] = None):
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
    url = f"{SLACK_API_BASE}/{method}"
    return requests.post(url, headers=headers, json=json_payload, data=data, files=files, timeout=30)


def slack_enabled() -> bool:
    return bool(SLACK_TOKEN and SLACK_CHANNEL)


def get_file_permalink_with_retry(file_id: str, tries: int = 6, sleep_s: float = 1.0) -> Optional[str]:
    for i in range(tries):
        r = slack_api("files.info", json_payload={"file": file_id})
        if r.ok:
            j = r.json()
            if j.get("ok") and j.get("file", {}).get("permalink"):
                return j["file"]["permalink"]
        time.sleep(sleep_s * (i + 1))
    return None


# =========================
# Introspection helpers
# =========================

def has_table(engine: Engine, table: str, schema: str = "public") -> bool:
    q = text("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = :schema AND table_name = :table
        LIMIT 1
    """)
    with engine.connect() as cx:
        return cx.execute(q, {"schema": schema, "table": table}).first() is not None


def has_column(engine: Engine, table: str, column: str, schema: str = "public") -> bool:
    q = text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table AND column_name = :col
        LIMIT 1
    """)
    with engine.connect() as cx:
        return cx.execute(q, {"schema": schema, "table": table, "col": column}).first() is not None


# =========================
# Queries
# =========================

@dataclass
class Summary:
    run_id: Optional[str]
    window_hours: int
    articles_total: int
    sources_top: List[Tuple[str, int]]
    by_day: List[Tuple[str, int]]
    entities_top: List[Tuple[str, str, int]]  # (name, type, count)


def resolve_window(engine: Engine, run_id: Optional[str]) -> Tuple[Optional[str], int]:
    """
    Si existe articles.run_id y viene run_id -> usar run_id.
    Si no, usar ventana por horas.
    """
    if run_id and has_column(engine, "articles", "run_id"):
        return run_id, 0
    return None, DEFAULT_WINDOW_HOURS


def fetch_summary(engine: Engine, run_id: Optional[str]) -> Summary:
    run_id_resolved, window_h = resolve_window(engine, run_id)

    where_parts = []
    params: Dict[str, Any] = {}

    if run_id_resolved:
        where_parts.append("a.run_id = :run_id")
        params["run_id"] = run_id_resolved
    else:
        # Preferimos scraped_at si existe, de lo contrario published_at, y si nada existe, no filtramos.
        if has_column(engine, "articles", "scraped_at"):
            where_parts.append("a.scraped_at >= (NOW() - (:window_h || ' hours')::interval)")
            params["window_h"] = window_h
        elif has_column(engine, "articles", "created_at"):
            where_parts.append("a.created_at >= (NOW() - (:window_h || ' hours')::interval)")
            params["window_h"] = window_h
        elif has_column(engine, "articles", "published_at"):
            where_parts.append("a.published_at >= (NOW() - (:window_h || ' hours')::interval)")
            params["window_h"] = window_h

    where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""

    q_total = text(f"SELECT COUNT(*) AS n FROM articles a {where_sql}")

    q_sources = text(f"""
        SELECT COALESCE(s.name, '—') AS source, COUNT(*) AS n
        FROM articles a
        LEFT JOIN sources s ON s.id = a.source_id
        {where_sql}
        GROUP BY 1
        ORDER BY n DESC
        LIMIT 12
    """)

    # Serie por día usando scraped_at si existe, si no published_at
    date_col = "a.scraped_at" if has_column(engine, "articles", "scraped_at") else "a.published_at"
    q_by_day = text(f"""
        SELECT TO_CHAR(DATE_TRUNC('day', {date_col}), 'YYYY-MM-DD') AS day, COUNT(*) AS n
        FROM articles a
        {where_sql}
        GROUP BY 1
        ORDER BY 1 ASC
        LIMIT 31
    """)

    # Entidades: preferimos entity_mentions (normalizado).
    entities_top: List[Tuple[str, str, int]] = []
    if has_table(engine, "entity_mentions") and has_table(engine, "entities"):
        # Si existe run_id en mentions, filtramos por run_id; si no, por join con artículos (si existe article_id)
        if run_id_resolved and has_column(engine, "entity_mentions", "run_id"):
            q_entities = text("""
                SELECT e.name, e.type, COUNT(*) AS n
                FROM entity_mentions em
                JOIN entities e ON e.id = em.entity_id
                WHERE em.run_id = :run_id
                GROUP BY 1,2
                ORDER BY n DESC
                LIMIT 20
            """)
            params_entities = {"run_id": run_id_resolved}
        elif has_column(engine, "entity_mentions", "article_id"):
            q_entities = text(f"""
                SELECT e.name, e.type, COUNT(*) AS n
                FROM entity_mentions em
                JOIN entities e ON e.id = em.entity_id
                JOIN articles a ON a.id = em.article_id
                {where_sql}
                GROUP BY 1,2
                ORDER BY n DESC
                LIMIT 20
            """)
            params_entities = params
        else:
            q_entities = None
            params_entities = {}
        if q_entities is not None:
            with engine.connect() as cx:
                rows = cx.execute(q_entities, params_entities).fetchall()
                entities_top = [(str(r[0]), str(r[1]), int(r[2])) for r in rows]

    with engine.connect() as cx:
        total = int(cx.execute(q_total, params).scalar() or 0)
        sources = [(str(r[0]), int(r[1])) for r in cx.execute(q_sources, params).fetchall()]
        by_day = [(str(r[0]), int(r[1])) for r in cx.execute(q_by_day, params).fetchall()]

    return Summary(
        run_id=run_id_resolved,
        window_hours=window_h,
        articles_total=total,
        sources_top=sources,
        by_day=by_day,
        entities_top=entities_top,
    )


# =========================
# Plotting
# =========================

def plot_bar(title: str, labels: Sequence[str], values: Sequence[int], out_path: str) -> Optional[str]:
    if plt is None:
        return None
    if not labels:
        return None

    plt.figure(figsize=(10, 4.5))
    plt.bar(range(len(labels)), list(values))
    plt.xticks(range(len(labels)), list(labels), rotation=45, ha="right")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()
    return out_path


def slack_upload_image(path: str, title: str) -> Optional[str]:
    """
    Sube imagen a Slack usando files.uploadV2 (y devuelve permalink cuando sea posible).
    """
    if not slack_enabled():
        return None

    # 1) get upload URL
    r1 = slack_api("files.getUploadURLExternal", data={"filename": os.path.basename(path), "length": os.path.getsize(path)})
    if not r1.ok:
        return None
    j1 = r1.json()
    if not j1.get("ok"):
        return None

    upload_url = j1["upload_url"]
    file_id = j1["file_id"]

    # 2) upload bytes to that URL
    with open(path, "rb") as f:
        r2 = requests.post(upload_url, data=f.read(), timeout=60)
        if not r2.ok:
            return None

    # 3) complete upload
    r3 = slack_api(
        "files.completeUploadExternal",
        json_payload={
            "files": [{"id": file_id, "title": title}],
            "channel_id": SLACK_CHANNEL,
            "initial_comment": title,
        },
    )
    if not r3.ok:
        return None
    j3 = r3.json()
    if not j3.get("ok"):
        return None

    return get_file_permalink_with_retry(file_id)


# =========================
# Rendering (Slack Blocks)
# =========================

def build_blocks(summary: Summary) -> List[dict]:
    title = "Resumen de scraping"
    subtitle = f"Run: {summary.run_id}" if summary.run_id else f"Ventana: últimas {summary.window_hours}h"

    lines = [f"*Total artículos:* {summary.articles_total}"]
    if summary.sources_top:
        lines.append("\n*Top fuentes:*")
        for s, n in summary.sources_top[:8]:
            lines.append(f"• {s}: {n}")

    if summary.entities_top:
        lines.append("\n*Top entidades (mentions):*")
        for name, typ, n in summary.entities_top[:10]:
            lines.append(f"• {name} ({typ}): {n}")
    else:
        lines.append("\n_Nota: no hay entity_mentions (aún) o no se registraron menciones normalizadas._")

    body = "\n".join(lines)

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": title}},
        {"type": "section", "text": {"type": "mrkdwn", "text": subtitle}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": body}},
    ]
    return blocks


def notify_summary(run_id: Optional[str] = None) -> None:
    try:
        engine = make_engine()
        summary = fetch_summary(engine, run_id)

        blocks = build_blocks(summary)

        # Charts (optional)
        img_links: List[str] = []
        if plt is not None:
            os.makedirs("tmp", exist_ok=True)

            if summary.by_day:
                labels = [d for d, _ in summary.by_day]
                values = [n for _, n in summary.by_day]
                p1 = plot_bar("Artículos por día", labels, values, "tmp/articles_by_day.png")
                if p1:
                    link = slack_upload_image(p1, "Gráfico: Artículos por día")
                    if link:
                        img_links.append(f"• <{link}|Artículos por día>")

            if summary.entities_top:
                labels = [f"{n}" for n, _, _ in summary.entities_top[:12]]
                values = [c for _, _, c in summary.entities_top[:12]]
                p2 = plot_bar("Top entidades (mentions)", labels, values, "tmp/top_entities.png")
                if p2:
                    link = slack_upload_image(p2, "Gráfico: Top entidades")
                    if link:
                        img_links.append(f"• <{link}|Top entidades>")

        if img_links:
            blocks.append({"type": "divider"})
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*Gráficos*\n" + "\n".join(img_links)}})

        if slack_enabled():
            r = slack_api("chat.postMessage", json_payload={"channel": SLACK_CHANNEL, "blocks": blocks, "text": "Resumen de scraping"})
            if not (r.ok and r.json().get("ok")):
                raise RuntimeError(f"Slack chat.postMessage falló: {r.status_code} {r.text}")
            if VERBOSE:
                print("✅ Notificación enviada a Slack.")
        else:
            print("ℹ️ Slack no configurado. Blocks preview:")
            print(json.dumps(blocks, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"❌ Error en notify_summary: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Notifica en Slack un resumen del scraping.")
    parser.add_argument("--run-id", dest="run_id", default=None, help="Run ID (opcional, si articles.run_id existe).")
    args = parser.parse_args()
    notify_summary(args.run_id)