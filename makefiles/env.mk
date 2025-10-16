# === Entorno (uv + Python 3.12) ===
.PHONY: os-deps uv-install venv install install-dev ensure-pip pydantic-deps \
        spacy-model spacy-model-lg torch-gpu

PY ?= 3.12
VENV ?= .venv
UV ?= uv
PYTHON ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

os-deps: ## Instalar dependencias de sistema (Ubuntu 24.04)
	sudo apt update
	sudo apt install -y \
	  build-essential libxml2-dev libxslt1-dev libjpeg-dev zlib1g-dev \
	  libpq-dev libffi-dev ffmpeg python3-venv python3-dev

uv-install: ## Instalar uv si no existe
	@command -v $(UV) >/dev/null 2>&1 || (curl -LsSf https://astral.sh/uv/install.sh | sh)

venv: uv-install ## Crear venv (idempotente) + asegurar pip/setuptools/wheel
	@if [ ! -d "$(VENV)" ]; then \
	  echo "🐍 Creando venv en $(VENV)"; \
	  UV_NO_PROMPT=1 $(UV) venv --python $(PY); \
	  . $(VENV)/bin/activate && python -m ensurepip --upgrade; \
	  . $(VENV)/bin/activate && python -m pip install --upgrade pip setuptools wheel; \
	else \
	  echo "♻️ Reusando venv existente en $(VENV)"; \
	fi

install: venv ## Instalar dependencias (producción)
	@if [ -f pyproject.toml ] && [ -f requirements.lock.txt ]; then \
	  . $(VENV)/bin/activate && $(UV) pip install -r requirements.lock.txt -c constraints.txt; \
	elif [ -f pyproject.toml ]; then \
	  . $(VENV)/bin/activate && $(UV) pip compile pyproject.toml -o requirements.lock.txt --generate-hashes; \
	  . $(VENV)/bin/activate && $(UV) pip install -r requirements.lock.txt -c constraints.txt; \
	else \
	  . $(VENV)/bin/activate && $(UV) pip install -r requirements.txt -c constraints.txt; \
	fi

install-dev: venv ## Instalar dependencias (desarrollo)
	@if [ -f requirements-dev.txt ]; then \
	  . $(VENV)/bin/activate && $(UV) pip install -r requirements-dev.txt -c constraints.txt; \
	elif [ -f pyproject.toml ] && [ -f requirements.lock.txt ]; then \
	  . $(VENV)/bin/activate && $(UV) pip install -r requirements.lock.txt -c constraints.txt; \
	elif [ -f pyproject.toml ]; then \
	  . $(VENV)/bin/activate && $(UV) pip compile pyproject.toml -o requirements.lock.txt --all-extras --generate-hashes; \
	  . $(VENV)/bin/activate && $(UV) pip install -r requirements.lock.txt -c constraints.txt; \
	else \
	  . $(VENV)/bin/activate && $(UV) pip install -r requirements.txt -c constraints.txt; \
	fi

# === VS Code friendly: (opcional) re‑asegurar pip en venv ===
ensure-pip: venv ## Añadir/actualizar pip/setuptools/wheel en el venv (idempotente)
	@. $(VENV)/bin/activate && python -m ensurepip --upgrade
	@. $(VENV)/bin/activate && python -m pip install --upgrade pip setuptools wheel

pydantic-deps: venv ## Instalar pydantic y pydantic-settings (útil para settings.py)
	@. $(VENV)/bin/activate && $(UV) pip install pydantic pydantic-settings

# === Modelos spaCy (instala si falta) ===
SPACY_ES_MD_URL := https://github.com/explosion/spacy-models/releases/download/es_core_news_md-3.8.0/es_core_news_md-3.8.0.tar.gz
SPACY_ES_LG_URL := https://github.com/explosion/spacy-models/releases/download/es_core_news_lg-3.8.0/es_core_news_lg-3.8.0.tar.gz

spacy-model: venv ## Instalar/validar spaCy y es_core_news_md
	@. $(VENV)/bin/activate && \
	if $(PYTHON) -c "import spacy" 2>/dev/null; then \
	  echo "✔ spaCy ya instalado"; \
	else \
	  echo "↻ Instalando spaCy..."; \
	  $(UV) pip install "spacy>=3.8.0,<3.9.0"; \
	fi && \
	if $(PYTHON) -c "import spacy; spacy.load('es_core_news_md')" 2>/dev/null; then \
	  echo "✔ spaCy es_core_news_md OK"; \
	else \
	  echo "↻ Instalando es_core_news_md..."; \
	  $(UV) pip install "es_core_news_md @ $(SPACY_ES_MD_URL)"; \
	  $(PYTHON) -c "import spacy; spacy.load('es_core_news_md'); print('✔ spaCy es_core_news_md OK')"; \
	fi

spacy-model-lg: venv ## (opcional) Instalar/validar es_core_news_lg
	@. $(VENV)/bin/activate && \
	if $(PYTHON) -c "import spacy; spacy.load('es_core_news_lg')" 2>/dev/null; then \
	  echo "✔ spaCy es_core_news_lg OK"; \
	else \
	  echo "↻ Instalando es_core_news_lg con uv pip..."; \
	  $(UV) pip install "es_core_news_lg @ $(SPACY_ES_LG_URL)"; \
	  $(PYTHON) -c "import spacy; spacy.load('es_core_news_lg'); print('✔ spaCy es_core_news_lg OK')"; \
	fi

# === PyTorch GPU (CUDA 12.4) ===
torch-gpu: venv ## Instalar PyTorch con soporte CUDA (RTX 5070)
	@. $(VENV)/bin/activate && $(UV) pip install --index-url https://download.pytorch.org/whl/cu124 torch torchvision torchaudio
