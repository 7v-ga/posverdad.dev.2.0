# 👩‍💻 Guía de desarrollo — Postverdad

Guía para preparar el entorno, correr pruebas y contribuir a **Postverdad** en local.

---

## 🔧 Requisitos

- Ubuntu 22.04+ (recomendado 24.04)  
- Python **3.12** con `venv` / `pip`  
- **Docker** + Docker Compose plugin  
- **GNU make**  
- Internet (descarga de modelos NLP)

> Opcional pero útil: acceso a Docker sin sudo  
> ```bash
> sudo usermod -aG docker "$USER"  # cierra sesión y vuelve a entrar
> ```

---

## ⚡️ Setup rápido (recomendado)

```bash
# instala dependencias del sistema, crea venv, instala deps Python y spaCy
make setup

# valida imports base
make health-check
```

### Servicios (DB/Redis con Docker)

```bash
make db-up
make db-wait      # espera a que Postgres responda (no falla si tarda)
```

### Esquema de base de datos

```bash
# ⚠️ destruye y recrea tablas si usas --reset
.venv/bin/python db/init_db.py --reset -y
```

Para bajar servicios:

```bash
make db-down
```

---

## 🧪 Testing y cobertura

Separación por tipo:

- **Unit** (rápidos, sin DB) → *default de `make test`*  
- **Integration** (requiere DB en Docker)

```bash
# unit (rápidos) - dispatcher por defecto
make test

# suite completa (unit + integration, acumula cobertura)
DEFAULT_TEST_SCOPE=all make test

# solo integration
make test-int

# solo unit explícito
make test-unit

# reporte HTML de cobertura
make coverage-html   # abre htmlcov/index.html

# limpiar artefactos de cobertura
make cov-clean

# fusionar varios runs de cobertura y generar HTML combinado
make merge-coverage
```

Correr un test/archivo puntual:

```bash
.venv/bin/pytest tests/unit/test_storage_helpers_unit.py::test_save_keywords_inserta_parametrizado
.venv/bin/pytest -m integration
```

---

## 🔄 Targets de reset

Estos comandos automatizan la limpieza del entorno y las pruebas:

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

> 🔎 En resumen:  
> - **reset-nodb** → unit puro.  
> - **reset** → unit (con flag opcional para DB).  
> - **reset-all** → unit + integration (siempre usa Docker y resetea esquema).

---

## 🧰 Setup manual (alternativa)

```bash
# entorno Python
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt -c constraints.txt
test -f requirements-dev.txt && pip install -r requirements-dev.txt -c constraints.txt

# modelo spaCy (español)
python -m spacy download es_core_news_md
```

---

## 🗂️ Estructura para desarrollo

```plaintext
scrapy_project/
  ├── spiders/
  ├── pipelines.py
  ├── nlp_orchestrator.py
  ├── nlp_transformers.py
  ├── preprocessor.py
  ├── framing_llm.py
  ├── storage.py
  └── storage_helpers.py

db/
  ├── init_db.py
  └── schema.sql

makefiles/           # lógica modular: db.mk, test.mk, etc.
scripts/             # utilidades: check_db.py, reportes, etc.
tests/
  ├── unit/
  └── integration/
```

---

## 🔁 Flujo de trabajo típico

```bash
git checkout main
git pull --ff-only

# nueva rama de trabajo
git checkout -b feat/mi-feature

# desarrolla, corre unit rápido
make test

# chequeo completo (unit + integration)
DEFAULT_TEST_SCOPE=all make test

git add -A
git commit -m "feat: agrega X"
git push -u origin feat/mi-feature
# abre PR
```

---

## 📐 Estilo y herramientas

```bash
# formateo
.venv/bin/black .
.venv/bin/isort .

# hooks opcionales
.venv/bin/pre-commit install
```

---

## 🗒️ Variables de entorno

Copia `.env.example` como `.env` y ajusta según tu entorno. Ejemplo:

```dotenv
POSTGRES_DB=postverdad
POSTGRES_USER=postverdad
POSTGRES_PASSWORD=postverdad
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# caches HF/Transformers (acelera descargas y CI)
HUGGINGFACE_HUB_CACHE=.cache/hf
TRANSFORMERS_CACHE=.cache/hf/transformers
SENTENCE_TRANSFORMERS_HOME=.cache/sentence-transformers

LOG_TO_CONSOLE=true
NOTIFY_CRITICAL=false
SLACK_WEBHOOK_URL=
SLACK_BOT_TOKEN=
SLACK_CHANNEL=
MAX_DUPLICATES_IN_A_ROW=10
```

---

## 🧯 Problemas comunes

**DB “connection refused”**  
```bash
make db-up && make db-wait
# o usa un reset completo:
make reset-all
python scripts/check_db.py
```

**Cobertura falla en integración aislada**  
`make test-int` ya usa `--cov-append`; ejecuta antes `make test` o directamente `make reset-all`.

**spaCy model no encontrado**  
```bash
make spacy-model
# o
python -m spacy download es_core_news_md
```

**Permisos de Docker**  
```bash
sudo usermod -aG docker "$USER"  # relogin
```

---

## 🤝 Contribuir

1. Crea una rama (`feat/*`, `fix/*`).  
2. Asegura que **unit** pase (`make test`).  
3. Antes de merge, valida **integration** (`DEFAULT_TEST_SCOPE=all make test` o `make reset-all`).  
4. Abre PR con descripción clara.

---

## 📬 Contacto

Desarrollado por **Gabriel Aguayo Young**  
[gabrielaguayo@7v.cl](mailto:gabrielaguayo@7v.cl)
