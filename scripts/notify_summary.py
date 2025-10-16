#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import requests
import pandas as pd
from textwrap import shorten
from sqlalchemy import create_engine, text

import matplotlib
matplotlib.use("Agg")  # backend sin X
import matplotlib.pyplot as plt

# ========= ENV =========
DATABASE_URL          = os.getenv("DATABASE_URL", "postgresql+psycopg://posverdad:posverdad@localhost:5432/posverdad")
SLACK_TOKEN           = os.getenv("SLACK_BOT_TOKEN", "").strip()
SLACK_USER_TOKEN      = os.getenv("SLACK_USER_TOKEN", "").strip()
SLACK_CHANNEL         = os.getenv("SLACK_CHANNEL", "").strip()
SLACK_CHANNEL_IS_ID   = os.getenv("SLACK_CHANNEL_IS_ID", "1") == "1"
VERBOSE               = os.getenv("VERBOSE", "1") == "1"

# ========= SQL =========
def _get_engine():
    return create_engine(DATABASE_URL, future=True)

def resolve_run_id(engine, run_id: str | None):
    """
    Si run_id viene vacío/None, intenta usar LAST_RUN_ID o el último en nlp_runs.
    """
    if run_id and run_id.strip():
        return run_id.strip()

    rid_env = os.getenv("LAST_RUN_ID", "").strip()
    if rid_env:
        return rid_env

    with engine.connect() as conn:
        q = text("""
          SELECT run_id
          FROM nlp_runs
          WHERE run_id IS NOT NULL
          ORDER BY COALESCE(started_at, date) DESC NULLS LAST
          LIMIT 1
        """)
        row = conn.execute(q).first()
        return row[0] if row else None

# ========= SLACK HELPER =========
def slack_api(method: str, *, params=None, data=None, json=None, timeout=30):
    """
    Llamada genérica a Slack Web API: https://slack.com/api/{method}
    Acepta params (query), data (form-encoded) o json (body).
    """
    url = f"https://slack.com/api/{method}"
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
    try:
        if json is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            r = requests.post(url, headers=headers, json=json, timeout=timeout)
        elif data is not None:
            r = requests.post(url, headers=headers, data=data, timeout=timeout)
        else:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
        return r
    except Exception as e:
        class Dummy:
            ok = False
            def json(self):
                return {"ok": False, "error": str(e)}
            text = str(e)
        return Dummy()

def slack_token_is_valid() -> bool:
    if not SLACK_TOKEN:
        return False
    r = slack_api("auth.test")
    ok = r.ok and r.json().get("ok")
    if VERBOSE:
        j = r.json() if r.ok else {}
        print(f"[SLACK] auth.test ok={ok} team={j.get('team')} user_id={j.get('user_id')} url={j.get('url')}")
    return ok

def slack_resolve_channel_id(name_or_id: str) -> str | None:
    """
    Si empieza con C/G asumimos ID y lo devolvemos.
    Si no, busca por nombre con conversations.list (channels:read / groups:read).
    """
    if not name_or_id:
        return None
    s = name_or_id.strip()
    if s.startswith(("C", "G")) and len(s) >= 9:
        return s

    next_cursor = None
    for _ in range(4):
        params = {
            "exclude_archived": "true",
            "limit": 200,
            "types": "public_channel,private_channel",
        }
        if next_cursor:
            params["cursor"] = next_cursor
        r = slack_api("conversations.list", params=params)
        if not (r.ok and r.json().get("ok")):
            break
        chans = r.json().get("channels", [])
        for c in chans:
            if c.get("name") == s:
                return c.get("id")
        next_cursor = r.json().get("response_metadata", {}).get("next_cursor")
        if not next_cursor:
            break
    return None

def slack_ensure_join(channel_id: str):
    r = slack_api("conversations.join", json={"channel": channel_id})
    if VERBOSE:
        if r.ok and r.json().get("ok"):
            print("[SLACK] conversations.join ok=True error=None")
        else:
            print(f"[SLACK] conversations.join ok=False error={r.json().get('error')}")

def slack_channel_info(channel_id: str):
    r = slack_api("conversations.info", params={"channel": channel_id})
    if VERBOSE:
        ok = r.ok and r.json().get("ok")
        ch = r.json().get("channel") if ok else None
        is_priv = None if not ch else ch.get("is_private")
        print(f"[SLACK] conversations.info ok={ok} channel={ch and ch.get('name')} is_private={is_priv}")

def upload_image(path, title, channel_id: str) -> dict:
    """
    Sube imagen con flujo EXTERNO:
      1) files.getUploadURLExternal
      2) PUT binario
      3) files.completeUploadExternal (publica el archivo en el canal)
    Retorna {ok: bool, file_id: str|None}
    """
    if not SLACK_TOKEN:
        print("❌ SLACK_BOT_TOKEN ausente")
        return {"ok": False, "file_id": None}
    if not channel_id:
        print("❌ channel_id requerido para subir imágenes")
        return {"ok": False, "file_id": None}
    if not slack_token_is_valid():
        print("❌ Token Slack inválido (auth.test falló)")
        return {"ok": False, "file_id": None}

    try:
        size = os.path.getsize(path)
        filename = os.path.basename(path)
        meta = {
            "filename": filename,
            "length": str(size),           # string
            "alt_text": title or filename,
        }
        # 1) URL de subida
        r1 = slack_api("files.getUploadURLExternal", data=meta)
        j1 = r1.json() if (r1.ok and "json" in r1.headers.get("content-type","")) else {}
        if not (r1.ok and j1.get("ok")):
            err = j1.get("error")
            print(f"⚠️ files.getUploadURLExternal falló: {r1.text}")
            if err in {"unknown_method", "method_deprecated"}:
                print("ℹ️ Tu workspace/token no soporta getUploadURLExternal. No se enviarán imágenes.")
            return {"ok": False, "file_id": None}

        upload_url = j1["upload_url"]
        file_id = j1["file_id"]

        # 2) PUT binario
        with open(path, "rb") as f:
            r2 = requests.put(upload_url, data=f, headers={"Content-Type": "application/octet-stream"}, timeout=60)
        if not (200 <= r2.status_code < 300):
            print(f"❌ PUT binario falló: HTTP {r2.status_code} {r2.text}")
            return {"ok": False, "file_id": None}

        # 3) Completar y publicar en canal
        r3 = slack_api("files.completeUploadExternal", data={
            "files": json.dumps([{"id": file_id, "title": title or filename}]),
            "channel_id": channel_id,
            "initial_comment": title or filename,
        })
        j3 = r3.json() if (r3.ok and "json" in r3.headers.get("content-type","")) else {}
        if not (r3.ok and j3.get("ok")):
            print(f"❌ files.completeUploadExternal falló: {r3.text}")
            return {"ok": False, "file_id": None}

        print(f"✅ Imagen subida al canal: {title or filename} → {channel_id} (file_id={file_id})")
        return {"ok": True, "file_id": file_id}

    except Exception as e:
        print(f"❌ Error al subir imagen: {e}")
        return {"ok": False, "file_id": None}

def get_file_permalink_with_retry(file_id: str, retries: int = 5, delay: float = 0.8) -> str | None:
    """
    Obtiene el permalink (autenticado) con reintentos.
    Requiere 'files:read'. Devuelve None si no disponible.
    """
    for i in range(retries):
        r = slack_api("files.info", params={"file": file_id})
        if r.ok and r.json().get("ok"):
            return r.json().get("file", {}).get("permalink")
        # file_not_found o aún no indexado
        time.sleep(delay)
    if VERBOSE:
        print(f"⚠️ files.info falló tras {retries} intentos")
    return None

# ========= LÓGICA DE NOTIFICACIÓN =========
def notify_summary(run_id: str | None):
    engine = _get_engine()
    rid = resolve_run_id(engine, run_id)

    if not rid:
        print("⚠️ No se encontró el run_id.")
        return

    try:
        # Consultas
        q_sum  = text("SELECT * FROM v_run_summary WHERE run_id = :rid")
        q_src  = text("SELECT * FROM v_run_top_sources WHERE run_id = :rid ORDER BY articles DESC")
        q_ent  = text("SELECT * FROM v_run_entities_top WHERE run_id = :rid ORDER BY mentions DESC")
        q_bins = text("SELECT * FROM v_run_sentiment_bins WHERE run_id = :rid ORDER BY metric, bucket")
        q_top  = text("SELECT * FROM v_run_top_articles WHERE run_id = :rid ORDER BY score DESC, len_chars DESC")

        df_sum  = pd.read_sql(q_sum,  engine, params={"rid": rid})
        df_src  = pd.read_sql(q_src,  engine, params={"rid": rid})
        df_ent  = pd.read_sql(q_ent,  engine, params={"rid": rid})
        df_bins = pd.read_sql(q_bins, engine, params={"rid": rid})
        df_top  = pd.read_sql(q_top,  engine, params={"rid": rid})

        if df_sum.empty:
            print("⚠️ No hay datos en v_run_summary para ese run_id. ¿Ejecutaste el pipeline?")
            return

        s = df_sum.iloc[0].to_dict()
        dur = int(s.get("duration_seconds") or 0)
        if dur < 3600:
            dur_fmt = f"{dur//60:02d}:{dur%60:02d}"
        else:
            dur_fmt = f"{int(dur//3600)}:{int((dur%3600)//60):02d}:{int(dur%60):02d}"

        # Top fuentes (máx 5)
        top_sources_lines = [f"• {r['source_name']}: {int(r['articles'])}" for _, r in df_src.head(5).iterrows()]
        top_sources_text = "\n".join(top_sources_lines) if top_sources_lines else "—"

        # Top entidades (máx 10)
        top_entities_lines = [f"• {r['entity_name']} ({r['entity_type']}): {int(r['mentions'])}" for _, r in df_ent.head(10).iterrows()]
        top_entities_text = "\n".join(top_entities_lines) if top_entities_lines else "—"

        # Top artículos (máx 5)
        top_articles_lines = []
        for _, r in df_top.head(5).iterrows():
            title = r.get("title") or "(sin título)"
            url   = r.get("url") or ""
            title_short = shorten(title, width=120, placeholder="…")
            top_articles_lines.append(f"• <{url}|{title_short}>" if url else f"• {title_short}")
        top_articles_text = "\n".join(top_articles_lines) if top_articles_lines else "—"

        # Buckets: polarity
        pol = df_bins[df_bins["metric"] == "polarity"]
        pol_order = ["very_negative","negative","neutral","positive","very_positive","unknown"]
        pol_counts = {b: 0 for b in pol_order}
        for _, r in pol.iterrows():
            pol_counts[str(r["bucket"])] = int(r["n"])
        pol_line = " | ".join([f"{k}:{v}" for k,v in pol_counts.items()])

        # KPIs (≤10 fields por sección)
        kpi_fields_part1 = [
            {"type": "mrkdwn", "text": f"*Insertados:* {int(s.get('total_inserted') or 0)}"},
            {"type": "mrkdwn", "text": f"*Descartados:* {int(s.get('total_discarded') or 0)}"},
            {"type": "mrkdwn", "text": f"*Actualizados:* {int(s.get('total_updated') or 0)}"},
            {"type": "mrkdwn", "text": f"*Errores:* {int(s.get('total_errors') or 0)}"},
            {"type": "mrkdwn", "text": f"*Duración:* {dur_fmt}"},
            {"type": "mrkdwn", "text": f"*Artículos:* {int(s.get('articles_count') or 0)}"},
            {"type": "mrkdwn", "text": f"*Fuentes:* {int(s.get('sources_count') or 0)}"},
            {"type": "mrkdwn", "text": f"*Items/min:* {s.get('items_per_minute') if s.get('items_per_minute') is not None else '—'}"},
        ]
        kpi_fields_part2 = [
            {"type": "mrkdwn", "text": f"*Avg len (chars):* {s.get('avg_len_chars') if s.get('avg_len_chars') is not None else '—'}"},
            {"type": "mrkdwn", "text": f"*P50 len:* {s.get('p50_len_chars') if s.get('p50_len_chars') is not None else '—'}"},
            {"type": "mrkdwn", "text": f"*Avg polarity:* {round(float(s.get('avg_polarity')),3) if s.get('avg_polarity') is not None else '—'}"},
            {"type": "mrkdwn", "text": f"*Avg subjectivity:* {round(float(s.get('avg_subjectivity')),3) if s.get('avg_subjectivity') is not None else '—'}"},
        ]
        if "discarded_duplicates" in df_sum.columns:
            dup = s.get("discarded_duplicates")
            kpi_fields_part2.append({"type": "mrkdwn", "text": f"*Desc. duplicados:* {int(dup) if dup is not None else '—'}"})
        if "discarded_invalid" in df_sum.columns:
            inv = s.get("discarded_invalid")
            kpi_fields_part2.append({"type": "mrkdwn", "text": f"*Desc. inválidos:* {int(inv) if inv is not None else '—'}"})

        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": f"Resumen corrida {rid}", "emoji": True}},
            {"type": "section", "fields": kpi_fields_part1},
            {"type": "section", "fields": kpi_fields_part2},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Top fuentes*"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": top_sources_text}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Top entidades (PERSON/ORG)*"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": top_entities_text}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Top artículos*"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": top_articles_text}},
            {"type": "context", "elements": [
                {"type": "mrkdwn", "text": f"*Polarity buckets:* {pol_line}"}
            ]}
        ]

        # === SLACK ===
        if SLACK_TOKEN and SLACK_CHANNEL and slack_token_is_valid():
            # Resolver canal
            if SLACK_CHANNEL_IS_ID and SLACK_CHANNEL.startswith(("C","G")):
                cid = SLACK_CHANNEL
                if VERBOSE:
                    print(f"[SLACK] chat.postMessage (ID-trust): canal_id={cid}")
            else:
                cid = slack_resolve_channel_id(SLACK_CHANNEL)

            if not cid:
                print("❌ No se pudo resolver SLACK_CHANNEL a un ID válido")
                return

            if VERBOSE:
                print(f"[SLACK] chat.postMessage → canal_id={cid} (origen='{SLACK_CHANNEL}')")
                slack_channel_info(cid)
            slack_ensure_join(cid)

            # Publicar resumen
            rmsg = slack_api("chat.postMessage", json={
                "channel": cid,
                "text": f"Resumen corrida {rid}",
                "blocks": blocks,
                "unfurl_links": False,
                "unfurl_media": False,
            })
            if not (rmsg.ok and rmsg.json().get("ok")):
                print(f"❌ Error al enviar mensaje: {rmsg.text}")
                return
            print("✅ Resumen enriquecido enviado a Slack")

            thread_ts = rmsg.json().get("ts")

            # Graficos (últimos 30 runs)
            df_all = pd.read_sql(text("""
                SELECT
                    COALESCE(date::date, started_at::date) AS fecha,
                    COALESCE(total_inserted, 0) AS total_inserted,
                    COALESCE(
                        duration_seconds,
                        EXTRACT(EPOCH FROM (finished_at - started_at))::int
                    ) AS duration_seconds
                FROM nlp_runs
                WHERE total_inserted IS NOT NULL
                ORDER BY COALESCE(date, started_at) DESC NULLS LAST
                LIMIT 30
            """), engine)

            if not df_all.empty:
                df_all['fecha'] = pd.to_datetime(df_all['fecha'])
                os.makedirs("graphs", exist_ok=True)

                # 1) Artículos por día
                plt.figure(figsize=(8,4))
                plt.plot(df_all['fecha'], df_all['total_inserted'], marker='o')
                plt.title("Artículos por día")
                plt.xlabel("Fecha")
                plt.xticks(rotation=45)
                plt.tight_layout()
                p1 = "graphs/slack_articulos_por_dia.png"
                plt.savefig(p1, dpi=144)
                plt.close()

                up1 = upload_image(p1, "Artículos por día", channel_id=cid)

                # 2) Duración por día
                plt.figure(figsize=(8,4))
                plt.bar(df_all['fecha'], df_all['duration_seconds'])
                plt.title("Duración por día")
                plt.xlabel("Fecha")
                plt.ylabel("Segundos")
                plt.xticks(rotation=45)
                plt.tight_layout()
                p2 = "graphs/slack_duracion_por_dia.png"
                plt.savefig(p2, dpi=144)
                plt.close()

                up2 = upload_image(p2, "Duración por día", channel_id=cid)

                # Publicar permalinks en hilo (si tenemos ts)
                if thread_ts:
                    # pequeño delay para indexación y evitar file_not_found
                    time.sleep(1.2)

                    if up1.get("ok") and up1.get("file_id"):
                        link1 = get_file_permalink_with_retry(up1["file_id"])
                        txt1 = "Gráfico: *Artículos por día*"
                        if link1:
                            txt1 += f" • <{link1}|ver imagen>"
                        m1 = slack_api("chat.postMessage", json={
                            "channel": cid, "thread_ts": thread_ts,
                            "text": txt1, "unfurl_links": False, "unfurl_media": False
                        })
                        if m1.ok and m1.json().get("ok"):
                            if VERBOSE:
                                print(f"✅ Enlace de imagen publicado en hilo: Artículos por día → {cid}")
                        else:
                            print(f"⚠️ chat.postMessage (link 1) falló: {m1.text}")

                    if up2.get("ok") and up2.get("file_id"):
                        link2 = get_file_permalink_with_retry(up2["file_id"])
                        txt2 = "Gráfico: *Duración por día*"
                        if link2:
                            txt2 += f" • <{link2}|ver imagen>"
                        m2 = slack_api("chat.postMessage", json={
                            "channel": cid, "thread_ts": thread_ts,
                            "text": txt2, "unfurl_links": False, "unfurl_media": False
                        })
                        if m2.ok and m2.json().get("ok"):
                            if VERBOSE:
                                print(f"✅ Enlace de imagen publicado en hilo: Duración por día → {cid}")
                        else:
                            print(f"⚠️ chat.postMessage (link 2) falló: {m2.text}")
                else:
                    print("ℹ️ No hay thread_ts del mensaje de resumen; no publicaré en hilo.")
            else:
                print("ℹ️ No hay datos suficientes para gráficos.")
        else:
            print("ℹ️ Slack no configurado o token inválido. Vista previa Blocks:")
            print(blocks)

    except Exception as e:
        print(f"❌ Error en notify_summary: {e}")

# ========= MAIN =========
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Notifica en Slack el resumen de un run_id")
    parser.add_argument("--run-id", dest="run_id", default=None, help="Run ID (opcional). Si no, usa LAST_RUN_ID o el último.")
    args = parser.parse_args()
    notify_summary(args.run_id)
