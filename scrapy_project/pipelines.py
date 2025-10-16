# scrapy_project/pipelines.py
import os
import uuid
import logging
from datetime import datetime
from hashlib import sha256
from time import monotonic

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import Json

from scrapy.exceptions import DropItem, CloseSpider
from dotenv import load_dotenv
from itemadapter import ItemAdapter

from .nlp_orchestrator import NLPOrchestrator
from .storage_helpers import store_article, save_entities, save_framing, _infer_domain_from_url

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
                logger.warning(f"[NLP] No se pudo cargar 'es_core_news_md': {e}. Fallback a blank('es')")
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

        # Orquestador con dependencias inyectadas
        self.nlp = NLPOrchestrator(
            spacy_model=spacy_model,
            posverdad_nlp=posverdad,
            preprocessor=preproc,
            framing_analyzer=None,  # activable más adelante sin coste de API
        )

    def _request_close(self, spider, reason: str):
        """Pide el cierre del spider al engine, solo una vez, y evita tracebacks."""
        if getattr(self, "_closing", False):
            return
        self._closing = True
        try:
            # Evita que se sigan programando nuevas requests y drena rápido.
            self.crawler.engine.close_spider(spider, reason=reason)
            logger.warning(f"[⛔] Cierre solicitado al engine. Motivo: {reason}")
        except Exception as e:
            logger.warning(f"[⛔] close_spider falló de forma no crítica: {e}")


    # ---------- Scrapy integration ----------
    @classmethod
    def from_crawler(cls, crawler):
        obj = cls()
        obj.crawler = crawler
        return obj

    def _bump(self, key: str, delta: int = 1):
        """Actualiza contadores en Scrapy Stats (visible en Dumping Scrapy stats)."""
        try:
            v = self.crawler.stats.get_value(key, 0) + delta
            self.crawler.stats.set_value(key, v)
        except Exception:
            pass

    # -------------------------
    # Ciclo de vida del spider
    # -------------------------
    def open_spider(self, spider):
        self._t0 = monotonic()
        # Conexión a Postgres
        try:
            self.conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )
            self.conn.autocommit = False  # transacciones manuales por ítem
            logger.info(
                "Conexión a la base de datos establecida. "
                f"host={POSTGRES_HOST} db={POSTGRES_DB} user={POSTGRES_USER}"
            )
        except OperationalError as e:
            logger.error(f"Fallo de conexión a Postgres: {e}")
            raise

        # Registrar RUN en nlp_runs
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO nlp_runs (run_id, started_at, status, notes)
                        VALUES (%s, NOW(), %s, %s)
                        ON CONFLICT (run_id) DO NOTHING
                        """,
                        (self.run_id, "running", f"Spider: {spider.name}"),
                    )
        except Exception as e:
            logger.warning(f"No se pudo registrar la corrida en nlp_runs: {e}")

        logger.info(f"[🆔] RUN_ID: {self.run_id}")

        # Warm-up de modelos (no bloqueante si falla)
        try:
            sample = "Warm-up: economía chilena y política pública."
            _ = self.nlp.analyze(sample)
            logger.info("[NLP] Warm-up completado.")
        except Exception as e:
            logger.warning(f"[NLP] Warm-up falló (no bloqueante): {e}")

    def close_spider(self, spider):
        # Cerrar con resumen
        try:
            duration_seconds = None
            try:
                duration_seconds = int(max(0, monotonic() - (self._t0 or monotonic())))
            except Exception:
                pass

            with self.conn:
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE nlp_runs
                           SET finished_at = NOW(),
                               status = %s,
                               notes  = %s,
                               total_inserted   = %s,
                               total_discarded  = %s,
                               total_updated    = %s,
                               total_errors     = %s,
                               duration_seconds = %s,
                               discarded_duplicates = %s,
                               discarded_invalid    = %s
                         WHERE run_id = %s
                        """,
                        (
                            "success",
                            f"inserted={self.inserted} "
                            f"updated={self.updated} "
                            f"discarded={self.discarded} "
                            f"errors={self.errors}",
                            self.inserted,
                            self.discarded,
                            self.updated,
                            self.errors,
                            duration_seconds,
                            self.discarded_duplicates,
                            self.discarded_invalid,
                            self.run_id,
                        ),
                    )
            resumen = (
                "\n🏁 Pipeline finalizado exitosamente.\n"
                f"🆔 RUN_ID registrado: {self.run_id}\n"
                f"✅ Insertados: {self.inserted}\n"
                f"📝 Actualizados: {self.updated}\n"
                f"🚫 Descartados: {self.discarded} "
                f"(inválidos={self.discarded_invalid}, duplicados_drop={self.discarded_duplicates})\n"
                f"❌ Errores: {self.errors}\n"
            )
            logger.info(resumen)
            with open(os.path.join(LOGS_DIR, "summary.log"), "a", encoding="utf-8") as fsum:
                fsum.write(resumen + "\n")
        except Exception as e:
            logger.warning(f"No se pudo actualizar nlp_runs: {e}")
        finally:
            try:
                if self.conn:
                    self.conn.close()
            except Exception:
                pass

        # Notificación opcional (no detiene cierre)
        try:
            import subprocess
            subprocess.run(
                ["python", "scripts/notify_summary.py", "--run-id", self.run_id],
                check=False
            )
        except Exception as e:
            logger.warning(f"❌ Error al notificar resumen: {e}")

    # -------------------------
    # Normalización defensiva
    # -------------------------
    @staticmethod
    def _normalize_item(item):
        """
        Normaliza el item para que el resto del pipeline pueda usar
        strings/arrays esperados (evita .strip() sobre listas, etc.).
        - Escalares típicos → str
        - body → str (join si viene lista)
        - authors/author → authors (list[str])
        - categories/category → categories (list[str])
        - meta_keywords → list[str]
        """
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
            # dedup preservando orden
            seen, res = set(), []
            for v in out:
                if v not in seen:
                    seen.add(v)
                    res.append(v)
            return res

        def _as_text(x):
            # Para body: si es lista, concatenar con espacios y limpiar
            if x is None:
                return ""
            if isinstance(x, (list, tuple)):
                parts = [str(p).strip() for p in x if str(p).strip()]
                return " ".join(parts).strip()
            return str(x).strip()

        # Escalares típicos
        for k in ("url", "title", "subtitle", "source", "domain", "image",
                  "meta_description", "publication_date", "published_at"):
            if k in adapter:
                adapter[k] = _as_str(adapter.get(k))

        # Cuerpo
        if "body" in adapter:
            adapter["body"] = _as_text(adapter.get("body"))

        # Autores
        if "authors" in adapter or "author" in adapter:
            authors_val = adapter.get("authors", None)
            if authors_val is None:
                authors_val = adapter.get("author", None)
            adapter["authors"] = _as_list_str(authors_val)
            if "author" in adapter:
                del adapter["author"]

        # Categorías
        if "categories" in adapter or "category" in adapter:
            cats_val = adapter.get("categories", None)
            if cats_val is None:
                cats_val = adapter.get("category", None)
            adapter["categories"] = _as_list_str(cats_val)
            if "category" in adapter:
                del adapter["category"]

        # Meta keywords → lista limpia
        if "meta_keywords" in adapter:
            adapter["meta_keywords"] = _as_list_str(adapter.get("meta_keywords"))

        return item

    # -------------------------
    # Validaciones y duplicados
    # -------------------------
    def _validate(self, item: dict):
        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()
        body = (item.get("body") or "").strip()
        if not url or not title or not body:
            raise DropItem("Campos requeridos vacíos (url/title/body)")
        if len(body) < MIN_BODY_LEN:
            raise DropItem(f"Article body too short (len={len(body)} < {MIN_BODY_LEN})")

    def _normalize_url_variants(self, url: str) -> list[str]:
        """
        Genera variantes canónicas: sin 'www.', con/sin slash final, http/https.
        """
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

            # variantes de host con/sin www.
            hosts = {netloc}
            if netloc.startswith("www."):
                hosts.add(netloc[4:])
            else:
                hosts.add("www." + netloc)

            # variantes de slash final en path
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
            # fallback simple si algo falla
            base = url.rstrip("/")
            alts = {url, base, base + "/"}
            if base.replace("://www.", "://") != base:
                alts.add(base.replace("://www.", "://"))
            if base.replace("://", "://www.") != base:
                alts.add(base.replace("://", "://www."))
            return list(alts)

    def _check_duplicates(self, cur, item: dict) -> str | None:
        """
        Retorna razón si es duplicado, None si no.
        Reglas:
          1) URL/url_canonical normalizadas
          2) body_hash
          3) dominio + título normalizado
        """
        url = (item.get("url") or "").strip()
        url_can = (item.get("url_canonical") or "").strip()
        title = (item.get("title") or "").strip()
        body = (item.get("body") or "").strip()

        # 1) URL variantes
        url_variants = self._normalize_url_variants(url)
        if url_can:
            url_variants.extend(self._normalize_url_variants(url_can))
        url_variants = list(dict.fromkeys(v for v in url_variants if v))  # dedup

        if url_variants:
            cur.execute(
                "SELECT id FROM articles WHERE url = ANY(%s) LIMIT 1",
                (url_variants,)
            )
            row = cur.fetchone()
            if row:
                return f"Duplicado URL (article_id={row[0]})"

        # 2) body_hash
        h = _hash_body(body)
        item["body_hash"] = h
        cur.execute("SELECT id FROM articles WHERE body_hash = %s LIMIT 1", (h,))
        row = cur.fetchone()
        if row:
            return f"Duplicado HASH (article_id={row[0]})"

        # 3) dominio + título normalizado
        dom = (item.get("domain") or "").lower()
        title_norm = " ".join(title.lower().split())
        if dom and title_norm:
            cur.execute(
                """
                SELECT a.id
                  FROM articles a
                 WHERE lower(a.domain) = %s
                   AND regexp_replace(lower(a.title), '\s+', ' ', 'g') = %s
                 LIMIT 1
                """,
                (dom, title_norm)
            )
            row = cur.fetchone()
            if row:
                return f"Duplicado (domain+title) (article_id={row[0]})"

        return None

    # ---------------
    # Proceso por ítem
    # ---------------
    def process_item(self, item, spider):
        # 1) Normalización
        item = self._normalize_item(item)

        title = (item.get("title") or "").strip()
        logger.info(f"[🟦] Procesando artículo: {title or '(sin título)'}")

        # 2) Validación
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
            # Un inválido NO cuenta como duplicado; resetea streak
            self.duplicates_in_a_row = 0
            raise

        # 3) Asegurar domain desde la URL si faltara
        if not item.get("domain"):
            u = (item.get("url") or "").strip()
            if u:
                item["domain"] = _infer_domain_from_url(u)

        # 4) Normalizar fecha canónica
        pub_date = (item.get("publication_date") or "").strip()
        pub_at   = (item.get("published_at") or "").strip()
        if pub_at:
            item["publication_date"] = pub_at[:10]
        elif pub_date:
            if not pub_date.endswith("Z"):
                item["published_at"] = f"{pub_date}T00:00:00Z"

        # 5) run_id
        item.setdefault("run_id", self.run_id)

        # === DUPLICADOS: evaluar y dropear antes del upsert ===
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    # 5.1) check duplicados (antes de guardar)
                    dup_reason = self._check_duplicates(cur, item)
                    if dup_reason:
                        self.discarded += 1
                        self.discarded_duplicates += 1
                        self._bump("posverdad/discarded_duplicates", 1)
                        self.duplicates_in_a_row += 1
                        
                        # Corte por total de duplicados
                        if MAX_DUPLICATES_TOTAL and self.discarded_duplicates >= MAX_DUPLICATES_TOTAL:
                            logger.warning(
                                f"Demasiados duplicados en total "
                                f"({self.discarded_duplicates} >= {MAX_DUPLICATES_TOTAL}). Solicitando cierre…"
                            )
                            self._request_close(spider, "too_many_duplicates_total")
                            # No llenamos el log con tracebacks: descartamos silenciosamente este y los siguientes ítems
                            raise DropItem("closing: too_many_duplicates_total")
                        
                        logger.info(
                            f"[🟠] Drop duplicado — {dup_reason}. "
                            f"streak={self.duplicates_in_a_row}/{MAX_DUPLICATES_IN_A_ROW}"
                        )
                        
                        # Corte por racha de duplicados consecutivos
                        if self.duplicates_in_a_row >= MAX_DUPLICATES_IN_A_ROW:
                            logger.warning(
                                f"Demasiados duplicados seguidos "
                                f"({self.duplicates_in_a_row} >= {MAX_DUPLICATES_IN_A_ROW}). Solicitando cierre…"
                            )
                            self._request_close(spider, "too_many_duplicates_in_a_row")
                            raise DropItem("closing: too_many_duplicates_in_a_row")
                        
                        # Si no se cierra aún, solo descartamos este duplicado
                        raise DropItem("duplicate")

                    logger.info("[3a] guardando artículo…")
                    try:
                        created = None
                        try:
                            res = store_article(cur, item, return_created=True)
                        except TypeError as te:
                            # Mocks antiguos no aceptan 'return_created'
                            if "return_created" in str(te):
                                res = store_article(cur, item)  # retorna solo id
                                created = None
                            else:
                                raise

                        if isinstance(res, tuple) and len(res) >= 2:
                            article_id, created = res[0], bool(res[1])
                        else:
                            article_id = res
                            # created permanece None si no vino

                        item["article_id"] = article_id
                        item["was_created"] = created  # True/False/None
                        logger.info(f"[3b] guardado id={article_id} created={created}")
                    except Exception as ins_exc:
                        self.errors += 1
                        logger.error(f"[3x] error al guardar: {ins_exc}")
                        raise

                    # Si es nuevo → NLP y relacionales
                    if created:
                        logger.info("[2] Ejecutando análisis NLP…")
                        preprocessed = {}
                        try:
                            text_for_nlp = (item.get("body") or "").strip()
                            if not text_for_nlp:
                                text_for_nlp = f"{(item.get('title') or '').strip()} {(item.get('subtitle') or '').strip()}".strip()
                            if text_for_nlp:
                                preprocessed = self.nlp.analyze(text_for_nlp) or {}
                        except Exception as nlp_exc:
                            logger.warning(f"[2] NLP falló: {nlp_exc}")
                            preprocessed = {}

                        # Limpieza/unificación opcional de entidades
                        try:
                            from importlib import import_module
                            clean_and_unify_entities = None
                            for _mod in ("scrapy_project.heuristica_entities", "scrapy_project.heuristics_entities"):
                                try:
                                    _m = import_module(_mod)
                                    clean_and_unify_entities = getattr(_m, "clean_and_unify_entities", None)
                                    if clean_and_unify_entities:
                                        break
                                except Exception:
                                    pass
                            if clean_and_unify_entities:
                                spacy_doc = None
                                text_for_doc = (item.get("body") or "").strip() or title
                                if self.spacy_model is not None and text_for_doc:
                                    try:
                                        spacy_doc = self.spacy_model(text_for_doc)
                                    except Exception:
                                        spacy_doc = None
                                if isinstance(preprocessed, dict) and preprocessed.get("entities"):
                                    preprocessed["entities"] = clean_and_unify_entities(
                                        preprocessed["entities"], spacy_doc=spacy_doc
                                    )
                                if item.get("entities"):
                                    item["entities"] = clean_and_unify_entities(item["entities"], spacy_doc=spacy_doc)
                        except Exception as e:
                            logger.warning(f"[entities] limpieza/unificación falló: {e}")

                        # Inyectar salidas del NLP al item si no estaban
                        if isinstance(preprocessed, dict) and preprocessed:
                            if "entities" in preprocessed and not item.get("entities"):
                                item["entities"] = preprocessed["entities"]
                            if "polarity" in preprocessed and item.get("polarity") is None:
                                item["polarity"] = preprocessed["polarity"]
                            if "subjectivity" in preprocessed and item.get("subjectivity") is None:
                                item["subjectivity"] = preprocessed["subjectivity"]
                            if "framing" in preprocessed and not item.get("framing"):
                                item["framing"] = preprocessed["framing"]

                        # Persistir preprocessed_data y relacionales
                        try:
                            cur.execute(
                                """
                                UPDATE articles
                                   SET preprocessed_data = %s
                                 WHERE id = %s
                                """,
                                (Json(preprocessed), article_id),
                            )
                            logger.info("[4b] preprocessed_data OK")

                            # Actualizar polarity/subjectivity si las tenemos
                            pol = item.get("polarity")
                            subj = item.get("subjectivity")
                            if pol is None and isinstance(preprocessed, dict):
                                pol = preprocessed.get("polarity")
                            if subj is None and isinstance(preprocessed, dict):
                                subj = preprocessed.get("subjectivity")

                            if pol is not None or subj is not None:
                                cur.execute(
                                    """
                                    UPDATE articles
                                       SET polarity     = COALESCE(%s, polarity),
                                           subjectivity = COALESCE(%s, subjectivity)
                                     WHERE id = %s
                                    """,
                                    (pol, subj, article_id),
                                )

                            # Entidades
                            ents = (item.get("entities") or preprocessed.get("entities") or [])
                            if ents:
                                try:
                                    save_entities(cur, article_id, ents)
                                    logger.info("[4c] entities OK")
                                except Exception as ee:
                                    logger.warning(f"[4x] fallo al guardar entities: {ee}")

                            # Framing
                            framing = item.get("framing") or preprocessed.get("framing") or {}
                            if framing:
                                try:
                                    save_framing(cur, article_id, framing)
                                    logger.info("[4d] framing OK")
                                except Exception as fe:
                                    logger.warning(f"[4x] fallo al guardar framing: {fe}")

                        except Exception as upd_exc:
                            logger.warning(f"[4x] fallo al actualizar preprocessed_data/relacionales: {upd_exc}")

            # ——— Fuera del with: COMMIT hecho ———

            created = item.get("was_created")
            created_effective = True if created is None else bool(created)

            if created_effective:
                # Nuevo → reset streak y contadores
                self.duplicates_in_a_row = 0
                self.inserted += 1
                self._bump("posverdad/inserted", 1)
                logger.info("[✔] commit realizado (nuevo)")
                logger.info(f"✅ Artículo NUEVO: {item['article_id']} — {title[:80]}")
            else:
                # Existente (upsert por conflicto) → cuenta como “updated”
                self.updated += 1
                self._bump("posverdad/updated", 1)
                # OJO: la racha de duplicados la gestiona EXCLUSIVAMENTE el branch de drop duplicado
                logger.info(f"[↩] Artículo ya existente (update por conflicto).")

            return item

        except DropItem:
            raise
        except CloseSpider:
            raise
        except Exception as e:
            self.errors += 1
            url = (item.get("url") or "").strip()
            logger.error(f"[💥] Error procesando ítem url={url}: {e}")
            raise
