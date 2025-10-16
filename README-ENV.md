# 🧪 Entorno — Postverdad (Ubuntu 24.04, 2025)

[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-orange)](https://ubuntu.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red)](https://redis.io/)

Guía de entorno para correr **Postverdad** en Ubuntu 24.04 con Python 3.12, Docker (PostgreSQL + Redis) y NLP (spaCy + pysentimiento).

---

## 📦 Requisitos del sistema

```bash
sudo apt update
sudo apt install -y build-essential git curl unzip make python3.12-venv python3-pip
```

### Docker (Engine + Compose plugin)

```bash
# llaves y repo de Docker
sudo apt install -y ca-certificates gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc >/dev/null
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

# instalar
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# (opcional) usar docker sin sudo
sudo usermod -aG docker "$USER"
# cierra sesión y vuelve a entrar (o reinicia)
```

### GPU (opcional, NVIDIA)

```bash
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -fsSL https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update && sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

> En `docker-compose.yml` ya se eliminó `version:` y `container_name:`. Usa `name: postverdad` y healthchecks.

---

## 📁 Repositorio y entorno Python

```bash
# clona el repo (SSH recomendado)
git clone git@github.com:<TU_ORG>/<TU_REPO>.git
cd <TU_REPO>

# crea venv y setup completo
make setup

# o manual (no recomendado):
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
make lock
make install
```

---

## 🔐 Variables de entorno (`.env`)

Copia `.env.example` a `.env` y ajusta. Ejemplo:

```dotenv
POSTGRES_DB=postverdad
POSTGRES_USER=postverdad
POSTGRES_PASSWORD=postverdad
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# caches HF/Transformers
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

## 🧱 Servicios con Docker

Levantar Postgres + Redis (espera healthchecks automáticamente):

```bash
make db-up
```

Inicializar esquema (⚠️ destructivo):

```bash
.venv/bin/python db/init_db.py --reset -y
```

Bajar servicios:

```bash
make db-down
```

Validar estado:

```bash
python scripts/check_db.py
```

---

## 🔄 Targets de reset

- `make reset` → Unit tests rápidos, sin DB (opcional `SCHEMA_RESET=1` para levantar DB y resetear esquema).  
- `make reset-all` → Siempre levanta DB/Redis con Docker, resetea esquema y corre unit + integration.  
- `make reset-nodb` → Solo unit tests, sin DB.

---

## 🧠 Modelos NLP y cachés

```bash
make spacy-model
mkdir -p .cache/hf .cache/hf/transformers .cache/sentence-transformers
```

---

## 🧪 Tests y cobertura

```bash
make test               # unit
DEFAULT_TEST_SCOPE=all make test   # unit + integration
make test-int           # solo integración
make coverage-html
```

> `make reset-all` limpia entorno, levanta DB y corre **unit + integration** con cobertura combinada.

---

## 🕸️ Scraping y pipeline

```bash
make scrape
./postverdad.sh
```

Con parámetros:

```bash
make scrape ARGS="-a year=2024 -a category=politica -a max_duplicates=15"
```

---

## 🛡️ Producción y rendimiento

- Usa Postgres 16 + Redis 7 (con healthchecks).  
- Para embeddings, habilita `pgvector`.  
- Caches NLP en volúmenes persistentes en contenedores.  
- En CI/CD, ejecuta `make reset-all` para validar unit + integration.

---

## 🧯 Problemas comunes

**Docker sin permisos**  
```bash
sudo usermod -aG docker "$USER"  # re-login
```

**DB “connection refused”**  
```bash
make db-up
python scripts/check_db.py
```

**Cobertura baja en integración aislada**  
Usa `make reset-all` (unit + integration, cobertura acumulada).

---

## 🧰 Chuleta rápida

```bash
make setup
make db-up
make reset-all
make test
make scrape
make coverage-html
```
