# 📰 Proyecto Posverdad

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-green)](https://docs.pytest.org/)
[![Coverage](https://img.shields.io/badge/coverage-%E2%89%A570%25-brightgreen)](https://coverage.readthedocs.io/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

Sistema automatizado de extracción, análisis y clasificación de noticias de medios chilenos. Incluye scraping, procesamiento NLP, análisis de sentimiento, encuadre ideológico, base de datos y notificaciones automáticas.

---

## Estructura

```plaintext
Posverdad/
.
├── backlog_github.csv
├── bootstrap_spider_tests.sh
├── constraints.txt
├── CONTRIBUTING.md
├── .coveragerc
├── db
│   ├── init_db.py
│   ├── schema.sql
│   └── seed_entities_aux.sql
├── docker-compose.yml
├── .env.example
├── .gitattributes
├── .github
│   ├── ISSUE_TEMPLATE
│   │   ├── bug.yml
│   │   ├── config.yml
│   │   └── feature.yml
│   ├── labeler.yml
│   ├── labels.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows
│       ├── autolabel.yml
│       └── stale.yml
├── .gitignore
├── import_issues.py
├── issues.csv
├── jobs
│   ├── al_add_missing_canonical_links.sql
│   ├── al_delete_alias_links.sql
│   ├── al_prune_añias_entities.sql
│   ├── bl_prune_orphan_entities.sql
│   ├── bl_unlink_blocked_links.sql
│   ├── prepare_indexes.sql
│   ├── reconcile_aliases.sql
│   ├── reconcile_blocklist.sql
│   └── reconcile_runner.py
├── Makefile
├── makefiles
│   ├── db.mk
│   ├── env.mk
│   ├── nlp.mk
│   ├── notify.mk
│   ├── reconcile.mk
│   ├── report.mk
│   ├── scrape.mk
│   ├── test.mk
│   └── util.mk
├── package.json
├── package-lock.json
├── postverdad_dash
│   ├── postverdad_dashboard.ipynb
│   ├── postverdad_dashboard_noviews.ipynb
│   ├── postverdad_entities_packA.ipynb
│   ├── postverdad_entities_packB.ipynb
│   ├── postverdad_entities_packC.ipynb
│   ├── postverdad_entities_packC_queries.sql
│   ├── postverdad_queries_no_views.sql
│   └── postverdad_views.sql
├── postverdad.sh
├── pytest.ini
├── README-dev.md
├── README-ENV.md
├── README.md
├── README-UPGRADE.md
├── requirements-dev.in
├── requirements-dev.lock.txt
├── requirements-dev.txt
├── requirements.in
├── requirements.lock.txt
├── requirements.txt
├── reset_env.sh
├── scrapy.cfg
├── scrapy_project
│   ├── framing_llm.py
│   ├── heuristica_entities.py
│   ├── __init__.py
│   ├── items.py
│   ├── middlewares.py
│   ├── nlp_orchestrator.py
│   ├── nlp_transformers.py
│   ├── pipelines.py
│   ├── preprocessor.py
│   ├── settings.py
│   ├── spiders
│   │   ├── el_mostrador.py
│   │   └── __init__.py
│   ├── storage_helpers.py
│   └── storage.py
├── scripts
│   ├── check_db.py
│   ├── check_vacios.py
│   ├── export_last_run.py
│   ├── fix_nltk_ssl.sh
│   ├── nlp_warmup.py
│   ├── notify_summary.py
│   ├── notify_test.py
│   ├── report_runs.py
│   ├── report_summary.py
│   ├── retry_bad_dates.py
│   └── wait_db.py
├── settings.py
├── setup_env.sh
├── spider_tests
│   └── README_tests.md
├── tests
│   ├── conftest.py
│   ├── integration
│   │   ├── test_nlp_orchestrator.py
│   │   ├── test_nlp_transformers.py
│   │   ├── test_preprocessor.py
│   │   ├── test_storage_main.py
│   │   ├── test_storage.py
│   │   ├── test_store_article_mocked.py
│   │   └── test_store_article.py
│   ├── spiders
│   │   ├── conftest.py
│   │   ├── fixtures
│   │   │   ├── article_2023_07_12.html
│   │   │   ├── listing_all_2023.html
│   │   │   ├── listing_all_2025.html
│   │   │   └── listing_mixed_2021_2025.html
│   │   ├── test_el_mostrador_collect_first_page.py
│   │   ├── test_el_mostrador_extract_years.py
│   │   └── test_el_mostrador_parse_article.py
│   └── unit
│       ├── test_framing_llm_extra.py
│       ├── test_heuristica_entities_unit.py
│       ├── test_nlp_orchestrator_adapter_and_faults.py
│       ├── test_nlp_orchestrator_branches.py
│       ├── test_nlp_orchestrator_formats.py
│       ├── test_nlp_orchestrator_more_branches.py
│       ├── test_nlp_orchestrator_more_edges.py
│       ├── test_nlp_orchestrator_unit.py
│       ├── test_nlp_prchestrator_formats_extra.py
│       ├── test_nlp_transformers_quick_wins.py
│       ├── test_nlp_transformers_unit.py
│       ├── test_npl_transformers_branches.py
│       ├── test_pipeline_dates_normalization.py
│       ├── test_pipeline_normaliza_item.py
│       ├── test_preprocessor_branches.py
│       ├── test_preprocessor_spacy_unit.py
│       ├── test_preprocessor_stanza_and_arrors.py
│       ├── test_preprocessor_stanza_import.py
│       ├── test_storage_authors.py
│       ├── test_storage_authors_split_list.py
│       ├── test_storage_categories.py
│       ├── test_storage_categories_unit.py
│       ├── test_storage_db_branching.py
│       ├── test_storage_edge_cases.py
│       ├── test_storage_entities.py
│       ├── test_storage_helpers_norm_unit.py
│       ├── test_storage_helpers_nullable.py
│       ├── test_storage_helpers_unit.py
│       ├── test_storage_keywords_empty.py
│       ├── test_storage_keywords_explode.py
│       ├── test_storage_keywords.py
│       ├── test_storage_nullable_float_edge.py
│       ├── test_storage_save_authors_empty.py
│       ├── test_storage_save_framing_empty.py
│       ├── test_storage_save_preprocessed_data_modes.py
│       ├── test_storage_save_preprocessed_unit.py
│       ├── test_storage_store_article_on_conflict.py
│       ├── test_storage_store_article_unkown_fallback.py
│       ├── test_storage_store_article_unkown_source.py
│       └── test_storage_upsert_minimal.py
└── views
    └── postverdad_views.sql
```

## 🧠 Características principales

- Scraping estructurado con **Scrapy**
- Análisis de sentimiento y subjetividad con **pysentimiento**
- NER y preprocesamiento con **spaCy**
- Módulo de **framing** (simulado/plug-in LLM)
- Base de datos **PostgreSQL** con esquema relacional
- Corte automático por **duplicados consecutivos**
- **Makefile** para orquestar ciclo completo (setup, tests, scraping, reportes)
- **Slack** para notificaciones (opcional)

---

## 🚀 Instalación rápida

```bash
# entorno completo (venv, deps, spaCy)
make setup

# servicios de datos (Docker)
make db-up

# (opcional y destructivo) re-crear esquema
.venv/bin/python db/init_db.py --reset -y

# verificación rápida
make test               # unit (rápidos)
DEFAULT_TEST_SCOPE=all make test   # suite completa (unit + integration)
```

---

## ⚙️ Uso habitual

```bash
make reset        # limpia y corre unit
make reset-all    # limpia, levanta DB y corre unit + integration (cobertura acumulada)
make scrape       # ejecutar spider principal
```

### 🔄 Detalle de resets

- `make reset`  
  - Limpia entorno y deps Python.  
  - Corre **solo tests unitarios** (rápidos, sin DB).  
  - Opcional: `make reset SCHEMA_RESET=1` → también levanta Docker y recrea esquema DB.

- `make reset-all`  
  - Limpia entorno y deps.  
  - **Siempre levanta DB/Redis con Docker**, espera salud y resetea el esquema.  
  - Corre **tests unit + integration**.

- `make reset-nodb`  
  - Igual que `reset`, pero explícitamente sin Docker.  
  - Solo tests unitarios.

---

## 🔧 Tareas adicionales útiles

- `make coverage-html` — Reporte HTML de cobertura (`htmlcov/index.html`)
- `make cov-clean` — Limpia artefactos de cobertura
- `make merge-coverage` — Combina coberturas de múltiples runs
- `make export-last-run` — Exporta resultados del último run
- `make retry-bad-dates` — Reintento de URLs con fechas problemáticas
- `make runs-report` — Resumen de corridas
- `make notify-test` / `make notify-last` — Notificaciones Slack

---

## 🏋️ Parámetros (`ARGS`) para el spider

```bash
make scrape ARGS="-a year=2024 -a category=politica -a max_duplicates=15"
```

| Bandera                    | Tipo   | Descripción                           |
| -------------------------- | ------ | ------------------------------------- |
| `-a year=YYYY`             | entero | Año mínimo permitido (default: 2020)  |
| `-a category=XXX`          | texto  | Filtro textual por categoría          |
| `-a custom_urls=file.csv`  | ruta   | Lista personalizada de URLs           |
| `-a max_duplicates=N`      | entero | Corte por duplicados consecutivos     |

---

## 🤎 Pruebas y cobertura

```bash
make test            # unit (por defecto)
make test-int        # integración (requiere DB)
make merge-coverage  # fusionar cobertura de varios runs
make coverage-html   # abrir reporte HTML
```

> `reset-all` corre unit + integration con cobertura acumulada (evita falsos negativos).

---

## 🧰 Variables de entorno

Copia `.env.example` como `.env` y ajusta:

```dotenv
POSTGRES_DB=posverdad
POSTGRES_USER=posverdad
POSTGRES_PASSWORD=posverdad
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

SLACK_WEBHOOK_URL=
SLACK_BOT_TOKEN=
SLACK_CHANNEL=#tu-canal

MAX_DUPLICATES_IN_A_ROW=10

# Caches de modelos (acelera descargas y CI)
HUGGINGFACE_HUB_CACHE=.cache/hf
TRANSFORMERS_CACHE=.cache/hf/transformers
SENTENCE_TRANSFORMERS_HOME=.cache/sentence-transformers
TOKENIZERS_PARALLELISM=false
```

---

## 🛠️ Arquitectura del sistema

- `spiders/`: spiders por medio
- `pipelines.py`: validación y orquestación de guardado
- `nlp_orchestrator.py`: orquesta spaCy/Transformers/LLM
- `nlp_transformers.py`: sentimiento y subjetividad
- `preprocessor.py`: utilidades de preprocesamiento
- `storage.py` / `storage_helpers.py`: persistencia en PostgreSQL
- `scripts/`: utilidades CLI y reportes
- `Makefile`: automatización del ciclo de vida

---

## 📜 Notas técnicas

Evita advertencias de paralelismo en HuggingFace:

```python
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
```

Conexión SQLAlchemy + pandas:

```python
from sqlalchemy import create_engine
engine = create_engine("postgresql+psycopg://user:pass@host:port/db")
df = pd.read_sql("SELECT * FROM nlp_runs", engine)
```

Transformers (evitar deprecaciones futuras):

```python
# Pasa clean_up_tokenization_spaces explícitamente al tokenizador/modelo
tokenizer(..., clean_up_tokenization_spaces=True)
```

---

## 🚀 Ejecución automatizada

```bash
./posverdad.sh
```

Este script ejecuta: limpieza → tests → scrape → notificación.

---

## 📄 Licencia y créditos

Proyecto desarrollado como parte de la investigación **Posverdad**.  
Por: **Gabriel Aguayo Young**  
Contacto: [gabrielaguayo@7v.cl](mailto:gabrielaguayo@7v.cl)  
Con herramientas de software libre.
