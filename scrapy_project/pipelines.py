# scrapy_project/pipelines.py
import os
import uuid
import logging
from datetime import datetime
from hashlib import sha256
from time import monotonic

import psycopg
from psycopg import OperationalError
from psycopg.types.json import Json

from scrapy.exceptions import DropItem, CloseSpider
import scrapy_project.pipelines as p
from dotenv import load_dotenv
from itemadapter import ItemAdapter

from .nlp_orchestrator import NLPOrchestrator
from .storage_helpers import store_article, save_entities, save_framing, _infer_domain_from_url

from contextlib import contextmanager, nullcontext

# === NLP locales
from .nlp_transformers import PosverdadNLP
from .preprocessor import Preprocessor

try:
    import spacy
except Exception:
    spacy = None

# =========================
# Configuración y utilidades
# =========================
load_dotenv()

LOGS_DIR = os.getenv("LOGS_DIR", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_TO_CONSOLE = (os.getenv("LOG_TO_CONSOLE", "true").lower() == "true")

MIN_BODY_LEN = int(os.getenv("MIN_BODY_LEN", "50"))

# Corte por duplicados (conservador por defecto)
MAX_DUPLICATES_IN_A_ROW = int(os.getenv("MAX_DUPLICATES_IN_A_ROW", "50"))
# Corte duro por total de duplicados (0 = desactivado)
MAX_DUPLICATES_TOTAL = int(os.getenv("MAX_DUPLICATES_TOTAL", "0"))

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "posverdad")
POSTGRES_USER = os.getenv("POSTGRES_USER", "posverdad")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "posverdad")

# Logger “humano”
RUN_TS = datetime.now().strftime("%Y%m%d-%H%M%S")
RUN_ID = f"{RUN_TS}-{uuid.uuid4().hex[:8]}"
LOG_HUMAN = os.path.join(LOGS_DIR, f"pipeline_{RUN_ID}.log")

logger = logging.getLogger("posverdad.pipeline")
logger.setLevel(logging.DEBUG)

logger.info(f"[DBG] pipelines module path: {p.__file__}")

_file_handler = logging.FileHandler(LOG_HUMAN, mode="a", encoding="utf-8")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(_file_handler)

if LOG_TO_CONSOLE:
    _console = logging.StreamHandler()
    _console.setLevel(logging.INFO)
    _console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(_console)
    logger.info("[👀] Consola activada para logs.")
else:
    logger.info("[🔇] Logging a consola desactivado.")

logger.info(f"[✅] Logging inicializado: {os.path.abspath(LOG_HUMAN)}")


def _hash_body(text: str) -> str:
    return sha256((text or "").encode("utf-8")).hexdigest()


# =========================
# Pipeline principal Scrapy
# =========================
class ScrapyProjectPipeline:
    def __init__(self):
        self.crawler = None
        self.conn = None
        self.run_id = RUN_ID

        # Contadores finos
        self.inserted = 0
        self.updated = 0
        self.discarded = 0
        self.discarded_duplicates = 0
        self.discarded_invalid = 0
        self.errors = 0
        self._closing = False

        self.duplicates_in_a_row = 0
        self._t0 = None

        # =========================
        # A4: Carga de modelos y cachés
        # =========================
        spacy_model = None
        if spacy is not None:
            try:
                spacy_model = spacy.load("es_core_news_md")
                logger.info("[NLP] spaCy 'es_core_news_md' cargado.")
            except Exception as e:
                logger.warning(
                    f"[NLP] No se pudo cargar 'es_core_news_md': {e}. Fallback a blank('es')"
                )
                try:
                    spacy_model = spacy.blank("es")
                    logger.info("[NLP] spaCy blank('es') cargado (sin NER/dep).")
                except Exception as e2:
                    logger.warning(f"[NLP] spaCy no disponible: {e2}")
                    spacy_model = None
        else:
            logger.warning("[NLP] spaCy no está instalado en este entorno.")

        # Guardar referencia para heurísticas posteriores
        self.spacy_model = spacy_model

        # =========================
        # A1: Inyección de backends locales (con fallback)
        # =========================
        posverdad = None
        try:
            posverdad = PosverdadNLP(nlp_model=spacy_model)
            logger.info("[NLP] PosverdadNLP inicializado (pysentimiento + spaCy).")
        except Exception as e:
            logger.warning(f"[NLP] PosverdadNLP no disponible: {e}")
            posverdad = None

        preproc = None
        try:
            preproc = Preprocessor(engine="spacy")
            logger.info("[NLP] Preprocessor(spacy) inicializado.")
        except Exception as e:
            logger.warning(f"[NLP] Preprocessor no disponible: {e}")
            preproc = None

        self.nlp = NLPOrchestrator(
            spacy_model=spacy_model,
            posverdad_nlp=posverdad,
            preprocessor=preproc,
            framing_analyzer=None,
        )

    # ---------- Scrapy integration ----------
    @classmethod
    def from_crawler(cls, crawler):
        obj = cls()
        obj.crawler = crawler
        return obj
    
    @contextmanager
    def _cursor_ctx(self):
        """
        Cursor context manager compatible con:
          - psycopg3: cursor.close()
          - mocks/tests: cursor puede NO ser context manager
        """
        cur = None
        try:
            cur = self.conn.cursor()
            yield cur
        finally:
            try:
                if cur is not None and hasattr(cur, "close"):
                    cur.close()
            except Exception:
                pass

    # ---------- Helpers de conexión y transacciones ----------
    def _bump(self, key: str, delta: int = 1):
        try:
            v = self.crawler.stats.get_value(key, 0) + delta
            self.crawler.stats.set_value(key, v)
        except Exception:
            pass

    def _request_close(self, spider, reason: str):
        if getattr(self, "_closing", False):
            return
        self._closing = True
        try:
            self.crawler.engine.close_spider(spider, reason=reason)
            logger.warning(f"[⛔] Cierre solicitado al engine. Motivo: {reason}")
        except Exception as e:
            logger.warning(f"[⛔] close_spider falló de forma no crítica: {e}")

    def _tx_ctx(self):
        """
        Devuelve un context manager de transacción compatible con:
          - psycopg3: conn.transaction()
          - fallback: conn como context manager (with conn:)
          - último recurso: nullcontext()
        """
        conn = getattr(self, "conn", None)
        if conn is None:
            return nullcontext()

        # psycopg3
        tx = getattr(conn, "transaction", None)
        if callable(tx):
            return conn.transaction()

        # psycopg2-style / otros: with conn:
        enter = getattr(conn, "__enter__", None)
        exit_ = getattr(conn, "__exit__", None)
        if callable(enter) and callable(exit_):
            return conn

        return nullcontext()


    def _rollback_if_needed(self, where: str = ""):
        """
        Rollback defensivo: SOLO ejecuta ROLLBACK si la transacción quedó abortada.
        En psycopg3, eso corresponde a TransactionStatus.INERROR.
    
        Este método:
          - no debe lanzar excepciones
          - no debe hacer rollback incondicional (eso puede deshacer inserts válidos)
        """
        conn = getattr(self, "conn", None)
        if conn is None:
            return
    
        try:
            # Algunos drivers exponen .closed
            if getattr(conn, "closed", False):
                return
    
            rb = getattr(conn, "rollback", None)
            if not callable(rb):
                return
    
            # --- psycopg3: transaction_status permite saber si está abortada ---
            try:
                from psycopg.pq import TransactionStatus  # psycopg3
                info = getattr(conn, "info", None)
                tx_status = getattr(info, "transaction_status", None) if info is not None else None
    
                # Solo si está abortada
                if tx_status == TransactionStatus.INERROR:
                    rb()
                    logger.debug(f"[DB] rollback defensivo ejecutado ({where}) tx_status=INERROR")
                return
    
            except Exception:
                # No se pudo inspeccionar estado: no hacemos rollback por defecto
                # porque sería destructivo (puede revertir inserts válidos).
                return
    
        except Exception as e:
            logger.debug(f"[DB] rollback defensivo falló {where}: {e}")
    

    def _best_effort(self, cur, label: str, fn):
        """
        Ejecuta fn() dentro de un SAVEPOINT.
        Si no se puede crear el savepoint, se omite el bloque (para no abortar la tx).
        """
        sp = f"sp_{label}".replace("-", "_").replace(" ", "_")

        try:
            cur.execute(f"SAVEPOINT {sp}")
        except Exception as e:
            logger.warning(f"[best-effort:{label}] no se pudo crear SAVEPOINT ({e}); omitiendo bloque.")
            return

        try:
            fn()
        except Exception as e:
            try:
                cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
            except Exception:
                pass
            logger.warning(f"[best-effort:{label}] rollback a savepoint por error: {e}")
        finally:
            try:
                cur.execute(f"RELEASE SAVEPOINT {sp}")
            except Exception:
                pass

    def _connect(self):
        self.conn = psycopg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )
        self.conn.autocommit = False

    def _ensure_conn(self):
        """
        En psycopg3 la conexión puede quedar cerrada (p.ej. por uso indebido de context manager,
        timeout, caída de red, reinicio PG).
        Este guard asegura una conexión abierta.
        """
        if self.conn is None:
            self._connect()
            logger.warning("[DB] Conexión creada (self.conn era None).")
            return
        try:
            if getattr(self.conn, "closed", False):
                self._connect()
                logger.warning("[DB] Reconectado a Postgres (conn estaba cerrada).")
        except Exception:
            # Conservador: ante duda, reconecta
            self._connect()
            logger.warning("[DB] Reconectado a Postgres (estado conn indeterminado).")

    # -------------------------
    # Ciclo de vida del spider
    # -------------------------
    def open_spider(self, spider):
        self._t0 = monotonic()
        try:
            self._connect()
            logger.info(
                "Conexión a la base de datos establecida. "
                f"host={POSTGRES_HOST} db={POSTGRES_DB} user={POSTGRES_USER}"
            )
        except OperationalError as e:
            logger.error(f"Fallo de conexión a Postgres: {e}")
            raise

        logger.info(f"[🆔] RUN_ID: {self.run_id}")
        logger.info(f"[DB] conectado host={POSTGRES_HOST} port={POSTGRES_PORT} db={POSTGRES_DB} user={POSTGRES_USER}")

        with self.conn.cursor() as cur:
            cur.execute("select current_database(), current_schema(), inet_server_addr(), inet_server_port()")
            dbname, schema, ip, port = cur.fetchone()
        logger.info(f"[DB] current_database={dbname} schema={schema} server={ip}:{port}")

        # Warm-up (no bloqueante)
        try:
            sample = "Warm-up: economía chilena y política pública."
            _ = self.nlp.analyze(sample)
            logger.info("[NLP] Warm-up completado.")
        except Exception as e:
            logger.warning(f"[NLP] Warm-up falló (no bloqueante): {e}")

    def close_spider(self, spider):
        """Cierra recursos del pipeline y emite resumen/notify si corresponde."""
        duration_seconds = None
        try:
            duration_seconds = int(max(0, monotonic() - (self._t0 or monotonic())))
        except Exception:
            pass

        if getattr(self, "notify_enabled", False):
            try:
                from notify_summary import notify_summary  # type: ignore

                notify_summary(
                    run_id=getattr(self, "run_id", None),
                    source=getattr(spider, "name", None),
                    duration_seconds=duration_seconds,
                )
            except Exception as e:
                logger.warning(f"❌ Error en notify_summary: {e}")

        try:
            if getattr(self, "conn", None):
                self.conn.close()
        except Exception:
            pass

    @staticmethod
    def _normalize_item(item):
        adapter = ItemAdapter(item)

        def _first(x):
            if x is None:
                return None
            if isinstance(x, (list, tuple)):
                return x[0] if x else None
            return x

        def _as_str(x):
            x = _first(x)
            if x is None:
                return ""
            if isinstance(x, str):
                return x.strip()
            return str(x).strip()

        def _as_list_str(x):
            if x is None:
                return []
            if isinstance(x, (list, tuple)):
                out = [str(v).strip() for v in x if str(v).strip()]
            else:
                s = str(x).strip()
                out = [s] if s else []
            seen, res = set(), []
            for v in out:
                if v not in seen:
                    seen.add(v)
                    res.append(v)
            return res

        def _as_text(x):
            if x is None:
                return ""
            if isinstance(x, (list, tuple)):
                parts = [str(p).strip() for p in x if str(p).strip()]
                return " ".join(parts).strip()
            return str(x).strip()

        for k in (
            "url",
            "title",
            "subtitle",
            "source",
            "domain",
            "image",
            "meta_description",
            "publication_date",
            "published_at",
        ):
            if k in adapter:
                adapter[k] = _as_str(adapter.get(k))

        if "body" in adapter:
            adapter["body"] = _as_text(adapter.get("body"))

        if "authors" in adapter or "author" in adapter:
            authors_val = adapter.get("authors", None)
            if authors_val is None:
                authors_val = adapter.get("author", None)
            adapter["authors"] = _as_list_str(authors_val)
            if "author" in adapter:
                del adapter["author"]

        if "categories" in adapter or "category" in adapter:
            cats_val = adapter.get("categories", None)
            if cats_val is None:
                cats_val = adapter.get("category", None)
            adapter["categories"] = _as_list_str(cats_val)
            if "category" in adapter:
                del adapter["category"]

        if "meta_keywords" in adapter:
            adapter["meta_keywords"] = _as_list_str(adapter.get("meta_keywords"))

        return item

    def _validate(self, item: dict):
        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()
        body = (item.get("body") or "").strip()
        if not url or not title or not body:
            raise DropItem("Campos requeridos vacíos (url/title/body)")
        if len(body) < MIN_BODY_LEN:
            raise DropItem(f"Article body too short (len={len(body)} < {MIN_BODY_LEN})")

    def _normalize_url_variants(self, url: str) -> list[str]:
        if not url:
            return []
        url = url.strip()
        if not url:
            return []
        try:
            from urllib.parse import urlparse, urlunparse

            u = urlparse(url)
            netloc = (u.netloc or "").lower()
            path = u.path or ""

            hosts = {netloc}
            if netloc.startswith("www."):
                hosts.add(netloc[4:])
            else:
                hosts.add("www." + netloc)

            paths = {path.rstrip("/"), path.rstrip("/") + "/"}
            paths.add(path or "/")
            paths.add((path or "/").rstrip("/"))

            variants = set()
            for h in hosts:
                for p in paths:
                    for sch in ("https", "http"):
                        variants.add(urlunparse((sch, h, p, "", "", "")))
            return list(variants)
        except Exception:
            base = url.rstrip("/")
            alts = {url, base, base + "/"}
            if base.replace("://www.", "://") != base:
                alts.add(base.replace("://www.", "://"))
            if base.replace("://", "://www.") != base:
                alts.add(base.replace("://", "://www."))
            return list(alts)

    def _check_duplicates(self, cur, item: dict) -> str | None:
        url = (item.get("url") or "").strip()
        url_can = (item.get("url_canonical") or "").strip()
        title = (item.get("title") or "").strip()
        body = (item.get("body") or "").strip()

        url_variants = self._normalize_url_variants(url)
        if url_can:
            url_variants.extend(self._normalize_url_variants(url_can))
        url_variants = list(dict.fromkeys(v for v in url_variants if v))

        if url_variants:
            cur.execute("SELECT id FROM articles WHERE url = ANY(%s) LIMIT 1", (url_variants,))
            row = cur.fetchone()
            if row:
                return f"Duplicado URL (article_id={row[0]})"

        h = _hash_body(body)
        item["body_hash"] = h
        cur.execute("SELECT id FROM articles WHERE body_hash = %s LIMIT 1", (h,))
        row = cur.fetchone()
        if row:
            return f"Duplicado HASH (article_id={row[0]})"

        dom = (item.get("domain") or "").lower()
        title_norm = " ".join(title.lower().split())
        if dom and title_norm:
            cur.execute(
                """
                SELECT a.id
                  FROM articles a
                 WHERE lower(a.domain) = %s
                   AND regexp_replace(lower(a.title), '\\s+', ' ', 'g') = %s
                 LIMIT 1
                """,
                (dom, title_norm),
            )
            row = cur.fetchone()
            if row:
                return f"Duplicado (domain+title) (article_id={row[0]})"

        return None

    # ---------------
    # Proceso por ítem
    # ---------------
    def process_item(self, item, spider):
        item = self._normalize_item(item)
    
        title = (item.get("title") or "").strip()
        logger.info(f"[🟦] Procesando artículo: {title or '(sin título)'}")
    
        # ---------- Validación ----------
        try:
            self._validate(item)
        except DropItem as e:
            self.discarded += 1
            self.discarded_invalid += 1
            self._bump("posverdad/discarded_invalid", 1)
            url = (item.get("url") or "").strip()
            body_len = len((item.get("body") or "").strip())
            logger.info(
                f"[🟡] Drop por validación — url={url} title={title[:80]} len(body)={body_len} motivo={e}"
            )
            self.duplicates_in_a_row = 0
            raise
        
        # ---------- Derivados simples ----------
        if not item.get("domain"):
            u = (item.get("url") or "").strip()
            if u:
                item["domain"] = _infer_domain_from_url(u)
    
        pub_date = (item.get("publication_date") or "").strip()
        pub_at = (item.get("published_at") or "").strip()
        if pub_at:
            item["publication_date"] = pub_at[:10]
        elif pub_date:
            item["published_at"] = f"{pub_date}T00:00:00Z"
    
        item.setdefault("run_id", self.run_id)
    
        # ---------- helpers ----------
        def _extract_sentiment(preprocessed: dict) -> tuple[float | None, float | None]:
            """
            Soporta múltiples shapes:
              - {"polarity": x, "subjectivity": y}
              - {"sentiment": {"polarity": x, "subjectivity": y}}
              - {"preprocessed": {"polarity": x, "subjectivity": y}}
            """
            if not isinstance(preprocessed, dict):
                return (None, None)
    
            pol = preprocessed.get("polarity")
            subj = preprocessed.get("subjectivity")
    
            if pol is None or subj is None:
                sent = preprocessed.get("sentiment")
                if isinstance(sent, dict):
                    pol = pol if pol is not None else sent.get("polarity")
                    subj = subj if subj is not None else sent.get("subjectivity")
    
            if pol is None or subj is None:
                inner = preprocessed.get("preprocessed")
                if isinstance(inner, dict):
                    pol = pol if pol is not None else inner.get("polarity")
                    subj = subj if subj is not None else inner.get("subjectivity")
    
            # normaliza numéricos
            def _as_float(x):
                if x is None:
                    return None
                try:
                    return float(x)
                except Exception:
                    return None
    
            return (_as_float(pol), _as_float(subj))
    
        def _extract_entities(preprocessed: dict) -> list[dict]:
            """
            Esperado por save_entities():
              - dicts con text/raw_text, label/raw_label, start/span_start, end/span_end
              - si vienen strings, las convertimos a {"text": "..."}
            """
            if not isinstance(preprocessed, dict):
                return []
    
            ents = preprocessed.get("entities")
            if ents is None:
                inner = preprocessed.get("preprocessed")
                if isinstance(inner, dict):
                    ents = inner.get("entities")
    
            if not ents:
                return []
    
            out: list[dict] = []
            if isinstance(ents, (list, tuple)):
                for e in ents:
                    if isinstance(e, str):
                        s = e.strip()
                        if s:
                            out.append({"text": s})
                    elif isinstance(e, dict):
                        out.append(e)
            return out
    
        # ---------- TX A: dedupe + core ----------
        def _do_tx_a():
            self._rollback_if_needed("pre-tx-a")
            with self._cursor_ctx() as cur:
                try:
                    dup_reason = self._check_duplicates(cur, item)
                    if dup_reason:
                        self.discarded += 1
                        self.discarded_duplicates += 1
                        self._bump("posverdad/discarded_duplicates", 1)
                        self.duplicates_in_a_row += 1
    
                        if MAX_DUPLICATES_TOTAL and self.discarded_duplicates >= MAX_DUPLICATES_TOTAL:
                            logger.warning(
                                f"Demasiados duplicados en total "
                                f"({self.discarded_duplicates} >= {MAX_DUPLICATES_TOTAL}). Solicitando cierre…"
                            )
                            self._request_close(spider, "too_many_duplicates_total")
                            raise DropItem("closing: too_many_duplicates_total")
    
                        logger.info(
                            f"[🟠] Drop duplicado — {dup_reason}. "
                            f"streak={self.duplicates_in_a_row}/{MAX_DUPLICATES_IN_A_ROW}"
                        )
    
                        if self.duplicates_in_a_row >= MAX_DUPLICATES_IN_A_ROW:
                            logger.warning(
                                f"Demasiados duplicados seguidos "
                                f"({self.duplicates_in_a_row} >= {MAX_DUPLICATES_IN_A_ROW}). Solicitando cierre…"
                            )
                            self._request_close(spider, "too_many_duplicates_in_a_row")
                            raise DropItem("closing: too_many_duplicates_in_a_row")
    
                        raise DropItem("duplicate")
    
                    logger.info("[3a] guardando artículo (core)…")
    
                    created = None
                    try:
                        res = store_article(cur, item, return_created=True)
                    except TypeError as te:
                        msg = str(te)
                        if "return_created" in msg or "unexpected keyword" in msg:
                            res = store_article(cur, item)
                        else:
                            raise
                        
                    if isinstance(res, tuple) and len(res) >= 2:
                        article_id = int(res[0])
                        created = bool(res[1]) if res[1] is not None else None
                    else:
                        article_id = int(res)
                        created = None
    
                    item["article_id"] = article_id
                    item["was_created"] = bool(created) if created is not None else None
    
                    self.conn.commit()
                    logger.info(f"[3b] guardado id={article_id} created={created}")
    
                except Exception:
                    self._rollback_if_needed("except-tx-a")
                    raise
                
        # ---------- TX B: updates + entidades ----------
        def _do_tx_b(preprocessed: dict):
            if item.get("was_created") is not True:
                return
    
            self._rollback_if_needed("pre-tx-b")
    
            pol, subj = _extract_sentiment(preprocessed)
            ents = _extract_entities(preprocessed)
    
            with self._cursor_ctx() as cur:
                try:
                    article_id = item["article_id"]
    
                    # preprocessed_data siempre se guarda como JSON (aunque venga vacío)
                    self._best_effort(
                        cur,
                        "preprocessed_data",
                        lambda: cur.execute(
                            """
                            UPDATE articles
                               SET preprocessed_data = %s
                             WHERE id = %s
                            """,
                            (Json(preprocessed if isinstance(preprocessed, dict) else {}), article_id),
                        ),
                    )
    
                    # Sentiment
                    if pol is not None or subj is not None:
                        self._best_effort(
                            cur,
                            "sentiment",
                            lambda: cur.execute(
                                """
                                UPDATE articles
                                   SET polarity = COALESCE(%s, polarity),
                                       subjectivity = COALESCE(%s, subjectivity)
                                 WHERE id = %s
                                """,
                                (pol, subj, article_id),
                            ),
                        )
    
                    # Entidades -> entity_mentions (MVP)
                    if ents:
                        self._best_effort(
                            cur,
                            "entities",
                            lambda: save_entities(cur, article_id, ents, replace=True),
                        )
    
                    self.conn.commit()
                    logger.info(
                        f"[3c] derivados guardados id={article_id} pol={pol} subj={subj} ents={len(ents)}"
                    )
    
                except Exception:
                    self._rollback_if_needed("except-tx-b")
                    raise
                
        # ---------- ejecución ----------
        try:
            # core
            _do_tx_a()
    
            # NLP (fuera de transacción)
            preprocessed: dict = {}
            if item.get("was_created") is True:
                try:
                    text_for_nlp = (item.get("body") or "").strip()
                    if not text_for_nlp:
                        text_for_nlp = f"{(item.get('title') or '').strip()} {(item.get('subtitle') or '').strip()}".strip()
    
                    if text_for_nlp:
                        logger.info("[2] Ejecutando análisis NLP…")
                        preprocessed = self.nlp.analyze(text_for_nlp) or {}
                    else:
                        preprocessed = {}
                except Exception as nlp_exc:
                    logger.warning(f"[2] NLP falló (no bloqueante): {nlp_exc}")
                    preprocessed = {}
    
            # derivados / relacionales
            _do_tx_b(preprocessed)
    
            self.inserted += 1
            self._bump("posverdad/inserted", 1)
            self.duplicates_in_a_row = 0
            return item
    
        except DropItem:
            raise
        except CloseSpider:
            raise
        except Exception as e:
            self.errors += 1
            url = (item.get("url") or "").strip()
            logger.error(f"[💥] Error procesando ítem url={url}: {e}")
            self._rollback_if_needed("post-exception")
            raise
        
