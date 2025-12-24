#!/usr/bin/env python3
"""scripts/report_runs.py

Reporte por ventana temporal (sin nlp_runs).

Este script reemplaza el antiguo "report_runs.py" basado en nlp_runs y genera un
reporte de ingesta usando scraped_at como criterio temporal.

Uso (ejemplos):
  python scripts/report_runs.py --since-hours 24
  python scripts/report_runs.py --since "2025-12-22T00:00:00Z" --until "2025-12-23T00:00:00Z"
  python scripts/report_runs.py --since-hours 6 --limit 15

Requiere:
  - DATABASE_URL en .env (ej: postgresql+psycopg://user:pass@localhost:5432/db)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import typer
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv


app = typer.Typer(add_completion=False)


def _parse_dt(value: str) -> datetime:
    """Parsea ISO8601. Acepta 'Z' y strings naive (se asumen UTC)."""
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_engine() -> Engine:
    load_dotenv()
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("POSTGRES_DSN")
    if not url:
        raise RuntimeError("DATABASE_URL no está configurado (revisa .env)")
    return create_engine(url, pool_pre_ping=True, future=True)


@dataclass(frozen=True)
class Window:
    since: datetime
    until: datetime


def _resolve_window(
    since: Optional[str],
    until: Optional[str],
    since_hours: Optional[int],
) -> Window:
    now = _utc_now()
    if since_hours is not None:
        s = now - timedelta(hours=since_hours)
    elif since:
        s = _parse_dt(since)
    else:
        # default razonable
        s = now - timedelta(hours=24)

    u = _parse_dt(until) if until else now
    if u <= s:
        raise typer.BadParameter("'until' debe ser mayor que 'since'")
    return Window(since=s, until=u)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _print_kv(k: str, v: str) -> None:
    typer.echo(f"{k}: {v}")


@app.command()
def main(
    since: Optional[str] = typer.Option(
        None,
        help="Inicio de ventana en ISO8601 (UTC recomendado). Ej: 2025-12-22T00:00:00Z",
    ),
    until: Optional[str] = typer.Option(
        None,
        help="Fin de ventana en ISO8601 (por defecto: ahora UTC). Ej: 2025-12-23T00:00:00Z",
    ),
    since_hours: Optional[int] = typer.Option(
        None,
        help="Alternativa a --since: ventana relativa hacia atrás (horas)",
        min=1,
    ),
    limit: int = typer.Option(10, help="Top N para tablas", min=1, max=200),
    include_entities: bool = typer.Option(True, help="Incluye ranking de entidades normalizadas"),
) -> None:
    """Genera reporte de ingesta por ventana temporal."""
    w = _resolve_window(since, until, since_hours)
    engine = _get_engine()

    typer.echo("\n=== Posverdad · Reporte por ventana ===")
    _print_kv("Desde", _fmt(w.since))
    _print_kv("Hasta", _fmt(w.until))
    typer.echo("")

    with engine.connect() as conn:
        # Conteos generales
        total = conn.execute(
            text(
                """
                SELECT COUNT(*)::int
                FROM articles
                WHERE scraped_at >= :since AND scraped_at < :until
                """
            ),
            {"since": w.since, "until": w.until},
        ).scalar_one()

        _print_kv("Artículos insertados (scraped_at en ventana)", str(total))

        # Top fuentes
        typer.echo("\n--- Top fuentes ---")
        rows = conn.execute(
            text(
                """
                SELECT COALESCE(s.name, 'Sin fuente') AS source, COUNT(*)::int AS n
                FROM articles a
                LEFT JOIN sources s ON s.id = a.source_id
                WHERE a.scraped_at >= :since AND a.scraped_at < :until
                GROUP BY 1
                ORDER BY n DESC, source ASC
                LIMIT :limit
                """
            ),
            {"since": w.since, "until": w.until, "limit": limit},
        ).fetchall()

        if not rows:
            typer.echo("(sin datos)")
        else:
            for r in rows:
                typer.echo(f"{r.source}: {r.n}")

        # Publicación: rango de published_at dentro de ventana (informativo)
        typer.echo("\n--- Publicación (published_at) dentro de la ventana (informativo) ---")
        pub = conn.execute(
            text(
                """
                SELECT
                  MIN(published_at) AS min_published_at,
                  MAX(published_at) AS max_published_at
                FROM articles
                WHERE scraped_at >= :since AND scraped_at < :until
                """
            ),
            {"since": w.since, "until": w.until},
        ).mappings().one()

        _print_kv("Min published_at", str(pub["min_published_at"]) if pub["min_published_at"] else "(null)")
        _print_kv("Max published_at", str(pub["max_published_at"]) if pub["max_published_at"] else "(null)")

        # Top entidades normalizadas (entities + articles_entities)
        if include_entities:
            typer.echo("\n--- Top entidades normalizadas ---")
            ents = conn.execute(
                text(
                    """
                    SELECT e.name, e.type, COUNT(*)::int AS mentions
                    FROM articles a
                    JOIN articles_entities ae ON ae.article_id = a.id
                    JOIN entities e ON e.id = ae.entity_id
                    WHERE a.scraped_at >= :since AND a.scraped_at < :until
                      AND COALESCE(e.blocked, false) = false
                    GROUP BY e.name, e.type
                    ORDER BY mentions DESC, e.name ASC
                    LIMIT :limit
                    """
                ),
                {"since": w.since, "until": w.until, "limit": limit},
            ).fetchall()

            if not ents:
                typer.echo("(sin entidades normalizadas en esta ventana)")
            else:
                for e in ents:
                    typer.echo(f"{e.name} [{e.type}] : {e.mentions}")

    typer.echo("\nOK\n")


if __name__ == "__main__":
    app()