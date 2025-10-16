#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import time
from pathlib import Path

import psycopg2


def log_event(**kv):
    print(json.dumps(kv, ensure_ascii=False), flush=True)


def set_timeouts(cur, statement_timeout_ms: int, lock_timeout_ms: int, app_name: str):
    # Aplica timeouts y application_name por transacción (SET LOCAL)
    cur.execute(f"SET LOCAL application_name = %s;", (app_name,))
    cur.execute(f"SET LOCAL statement_timeout = {int(statement_timeout_ms)};")
    cur.execute(f"SET LOCAL lock_timeout = {int(lock_timeout_ms)};")


def run_batches(conn,
                sql_path: Path,
                label: str,
                max_batches: int = 1000,
                sleep_ms: int = 0,
                statement_timeout_ms: int = 60000,
                lock_timeout_ms: int = 5000,
                app_name: str = "posverdad.reconcile",
                dry_run: bool = False):
    """
    Ejecuta el SQL en bucle. Cada ejecución del archivo debe retornar UNA fila con UNA columna
    numérica 'affected' (o al menos una columna convertible a int) para indicar cuántas filas
    modificó ese batch. Se corta cuando affected == 0 o al llegar a max_batches.
    """
    sql_text = sql_path.read_text(encoding="utf-8")
    total = 0
    batches = 0

    while True:
        if batches >= max_batches:
            log_event(event="reconcile.max_batches_reached", label=label, max_batches=max_batches, total_affected=total)
            break

        t0 = time.time()
        affected = 0

        with conn.cursor() as cur:
            set_timeouts(cur, statement_timeout_ms, lock_timeout_ms, app_name)

            if dry_run:
                # No ejecutamos DML en dry-run. Solo registramos que lo omitiríamos.
                log_event(event="reconcile.dry_run_skip", label=label, sql=str(sql_path))
                # En dry-run, cortamos en 1 iteración para no spammear
                break

            cur.execute(sql_text)

            # Intentamos leer una fila con el conteo
            row = None
            try:
                row = cur.fetchone()
            except Exception:
                # Puede que el SQL no retorne nada; caemos al rowcount
                row = None

            if row is not None and len(row) >= 1 and row[0] is not None:
                try:
                    affected = int(row[0])
                except Exception:
                    affected = 0
            else:
                # Fallback: rowcount de la última sentencia (menos fiable)
                affected = int(cur.rowcount) if cur.rowcount is not None else 0

        conn.commit()

        batches += 1
        total += affected
        log_event(
            event="reconcile.batch",
            label=label,
            sql=str(sql_path.name),
            batch=batches,
            affected=affected,
            total_affected=total,
            duration_ms=int((time.time() - t0) * 1000),
        )

        if affected == 0:
            break

        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000.0)

    log_event(event="reconcile.done", label=label, total_affected=total, batches=batches)
    return total, batches


def main():
    parser = argparse.ArgumentParser(description="Posverdad DB Reconciliations (blocklist & aliases)")
    parser.add_argument("--dsn", default=os.getenv("POSTVERDAD_DSN", "dbname=posverdad user=postgres"),
                        help="DSN de conexión (por defecto toma POSTVERDAD_DSN)")
    parser.add_argument("--jobs-dir", default=None, help="Directorio de jobs SQL (por defecto: junto a este script)")
    parser.add_argument("--only", choices=["all", "blocklist", "aliases"], default="all",
                        help="Elegir qué reconciliar")
    parser.add_argument("--max-batches", type=int, default=1000, help="Máximo de iteraciones por archivo SQL")
    parser.add_argument("--sleep-ms", type=int, default=0, help="Sleep entre batches")
    parser.add_argument("--statement-timeout-ms", type=int, default=60000, help="statement_timeout por batch")
    parser.add_argument("--lock-timeout-ms", type=int, default=5000, help="lock_timeout por batch")
    parser.add_argument("--dry-run", action="store_true", help="No ejecuta DML, solo loguea")
    args = parser.parse_args()

    base_dir = Path(args.jobs_dir) if args.jobs_dir else Path(__file__).resolve().parent
    sql_dir = base_dir / "jobs"

    # Definimos tareas (cada archivo devuelve una fila con 'affected' por batch)
    blocklist_tasks = [
        ("blocklist.unlink_blocked_links", sql_dir / "bl_unlink_blocked_links.sql"),
        ("blocklist.prune_orphan_entities", sql_dir / "bl_prune_orphan_entities.sql"),
    ]
    aliases_tasks = [
        ("aliases.add_missing_canonical_links", sql_dir / "al_add_missing_canonical_links.sql"),
        ("aliases.delete_alias_links", sql_dir / "al_delete_alias_links.sql"),
        ("aliases.prune_alias_entities", sql_dir / "al_prune_alias_entities.sql"),
    ]

    if args.only == "blocklist":
        tasks = blocklist_tasks
    elif args.only == "aliases":
        tasks = aliases_tasks
    else:
        tasks = blocklist_tasks + aliases_tasks

    log_event(event="reconcile.start",
              dsn_alias=os.getenv("POSTVERDAD_DSN_ALIAS", ""),
              only=args.only,
              max_batches=args.max_batches,
              sleep_ms=args.sleep_ms,
              statement_timeout_ms=args.statement_timeout_ms,
              lock_timeout_ms=args.lock_timeout_ms,
              jobs_dir=str(sql_dir))

    conn = psycopg2.connect(args.dsn)
    try:
        for label, path in tasks:
            if not path.exists():
                log_event(event="reconcile.error", label=label, error=f"SQL file not found: {path}")
                continue

            run_batches(
                conn,
                sql_path=path,
                label=label,
                max_batches=args.max_batches,
                sleep_ms=args.sleep_ms,
                statement_timeout_ms=args.statement_timeout_ms,
                lock_timeout_ms=args.lock_timeout_ms,
                app_name=f"posverdad.reconcile.{label}",
                dry_run=args.dry_run,
            )
    finally:
        conn.close()
        log_event(event="reconcile.exit")

    return 0


if __name__ == "__main__":
    sys.exit(main())
