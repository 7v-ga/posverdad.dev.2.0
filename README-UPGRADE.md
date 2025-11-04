# 🔼 Guía de actualización — Posverdad (Ubuntu 24.04 / Python 3.12)

Esta guía explica **qué cambió**, **cómo actualizar tu entorno** y **qué rupturas** debes considerar al migrar a la versión actual de Posverdad.

---

## 📌 Resumen de cambios clave

- **Python 3.12** como runtime recomendado (se admite 3.10+).
- **Makefiles modularizados**: targets `reset`, `reset-all`, `test`, `test-unit`, `test-int`, `db-up`, `db-wait`, `db-down`, etc.
- **Testing separado** por tipo:
  - **unit** (rápidos, sin DB) por defecto en `make test`.
  - **integration** (requiere DB). En `reset-all` la cobertura **se acumula** (`--cov-append`) para evitar falsos negativos.
- **Almacenamiento**: helpers aceptan **`conn` o `cursor`**:
  - Si pasas **`conn`**: el helper hace `commit()`/`rollback()` internamente.
  - Si pasas **`cursor`**: **no** comitea (útil dentro de transacciones externas).
- **Transformers**: fijado a una versión compatible con Py3.12 (ejemplo: `4.44.x`); se recomienda pin explícito.
- **Torch**: instalación **opcional** y **separada** por CPU/GPU. No fijamos un número inexistente en PyPI.
- **spaCy**: modelo `es_core_news_md` requerido. Descarga automatizada vía `make setup`/`make spacy-model`.
- **Warnings de HuggingFace**: se recomienda pasar explícitamente `clean_up_tokenization_spaces=True/False` para evitar deprecaciones.
- **Cobertura**: `.coveragerc` recomendado y `pytest.ini` ajustado a markers/umbral.

---

## ✅ Checklist de upgrade (mínimo viable)

> Ejecuta estos pasos dentro del repo del proyecto.

```bash
# 1) Actualiza tu árbol y crea un backup de tu .env
git checkout main
git pull --ff-only
cp -n .env .env.backup.$(date +%Y%m%d) 2>/dev/null || true

# 2) Crea/renueva venv en Python 3.12
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip

# 3) Instala dependencias con constraints
pip install -r requirements.txt -c constraints.txt
test -f requirements-dev.txt && pip install -r requirements-dev.txt -c constraints.txt

# 4) Descarga modelo spaCy español
python -m spacy download es_core_news_md

# 5) Levanta servicios y espera DB
make db-up
make db-wait

# 6) (Opcional/Destructivo) Re-crear esquema
.venv/bin/python db/init_db.py --reset -y

# 7) Limpia artefactos de cobertura antiguos
make cov-clean

# 8) Corre unit (rápidos)
make test

# 9) Corre suite completa (unit + integration con cobertura acumulada)
DEFAULT_TEST_SCOPE=all make test
# o el pipeline completo
make reset-all
```

---

## 🧩 Cambios en dependencias

### Transformers

- Pin sugerido (ejemplo): `transformers==4.44.2`
- Motivo: compatibilidad estable con Py3.12/spaCy y evitar deprecaciones “silenciosas”.

### Torch (opcional, por CPU/GPU)

Instálalo **aparte**, **según tu hardware**:

```bash
# CPU (rueda oficial)
pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio

# NVIDIA CUDA 12.x (ajusta a tu versión CUDA)
pip install --index-url https://download.pytorch.org/whl/cu124 torch torchvision torchaudio
```

> Si no haces deep learning local, puedes omitir Torch.

### spaCy

- Asegura el modelo:

```bash
python -m spacy download es_core_news_md
```

---

## ⚙️ Makefiles y targets nuevos

```bash
make setup          # venv + deps + modelo spaCy
make reset          # limpia y corre unit
make reset-all      # limpia, levanta DB y corre unit + integration (cobertura acumulada)
make db-up          # levanta Postgres/Redis
make db-wait        # espera Postgres (no falla si tarda)
make db-down        # baja servicios
make test           # dispatcher (unit por defecto)
make test-int       # solo integración (usa --cov-append)
make coverage-html  # reporte HTML de cobertura
make cov-clean      # limpia artefactos de cobertura
make merge-coverage # combina .coverage.* y genera HTML combinado
```

> `make test` usa `DEFAULT_TEST_SCOPE=unit` por defecto. Para correr todo:  
> `DEFAULT_TEST_SCOPE=all make test`

---

## 🗄️ Cambios en almacenamiento (⚠️ posibles rupturas)

### Nuevo patrón de transacciones

- Los helpers (`save_keywords`, `save_entities`, `save_framing`, etc.) **aceptan `conn` o `cursor`**:
  - Si **`conn`** → el helper **comitea** al final y hace `rollback()` si falla.
  - Si **`cursor`** → no comitea (pensado para usarse dentro de `with conn:` o cuando tú controlas la transacción).
- **`store_article(conn, item)`** mantiene la transacción del alta completa y hace `commit()`/`rollback()`.

### Qué revisar en tu código

- Si antes asumías que **ningún** helper hacía `commit()`, y ahora pasas `conn`, puede cambiar el comportamiento.
  - **Solución**: pásales **`cursor`** si quieres controlar la transacción externamente:
    ```python
    with conn:
        with conn.cursor() as cur:
            save_keywords(cur, article_id, "a,b,c")
            save_entities(cur, article_id, ents)
    ```

---

## 🧪 Testing y cobertura

- **Markers**: `unit` y `integration` (ver carpeta `tests/unit` y `tests/integration`).
- **Cobertura**: en `reset-all` se corre `unit` y luego `integration` con `--cov-append` para acumular resultados.
- Umbral configurado en `pytest.ini` (`--cov-fail-under`); puedes ajustarlo según tus necesidades.

Ejemplos útiles:

```bash
# solo unit
make test

# solo integration (requiere DB arriba)
make test-int

# suite completa
DEFAULT_TEST_SCOPE=all make test
# o
make reset-all
```

---

## 🧠 HuggingFace / Transformers

- Evita warnings futuros pasando explícitamente `clean_up_tokenization_spaces=True/False` en tus llamadas de tokenización.
- En entornos con proxies/descargas lentas, usa caches:

```dotenv
HUGGINGFACE_HUB_CACHE=.cache/hf
TRANSFORMERS_CACHE=.cache/hf/transformers
SENTENCE_TRANSFORMERS_HOME=.cache/sentence-transformers
```

---

## 🧯 Problemas comunes

**DB “connection refused”**

```bash
make db-up && make db-wait
python scripts/check_db.py
```

Revisa además `POSTGRES_*` en `.env`.

**Cobertura < umbral al correr solo integración**  
Ejecuta `make test` primero o usa `make reset-all` (acumula cobertura).

**spaCy “model not found”**

```bash
python -m spacy download es_core_news_md
```

**Permisos Docker**

```bash
sudo usermod -aG docker "$USER"  # re-login
```

---

## 🧰 Extra: instalación con `uv` (opcional)

```bash
# instalar uv (si no lo tienes)
curl -LsSf https://astral.sh/uv/install.sh | sh

# crear venv y resolver deps con hashes reproducibles
uv venv --python 3.12
source .venv/bin/activate

uv pip install -r requirements.txt -c constraints.txt
test -f requirements-dev.txt && uv pip install -r requirements-dev.txt -c constraints.txt

# lock reproducible
uv pip compile requirements-dev.txt -o requirements.lock.txt --generate-hashes
uv pip install -r requirements.lock.txt
```

---

## 📝 Anexos (cambios mínimos en código)

- `preprocessor.py`: default `engine="spacy"`; Stanza opcional, descarga on-demand.
- `nlp_transformers.py`: manejo robusto cuando no hay modelos (retorna `None` o tuplas nulas).
- `nlp_orchestrator.py`: orquesta spaCy/transformers/preprocesador; captura y loguea excepciones internas para no romper pipeline.
- `pipelines.py`: uso de `with conn:` recomendado en procesos batch; log unificado y `RUN_ID` registrado en `nlp_runs`.

---

**Listo.** Si mantienes este checklist y los nuevos targets de Make, el upgrade queda estable y reproducible. Si necesitas un script `make upgrade-local` que automatice los pasos 1–9, lo dejamos en un commit aparte.
