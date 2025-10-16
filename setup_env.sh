#!/bin/bash

echo "🐍 Verificando entorno virtual..."
if [ ! -d "venv" ]; then
    echo "➕ Creando entorno virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements-dev.txt -c constraints.txt

echo "📚 Verificando modelo spaCy..."
python -m spacy validate | grep es_core_news_md || python -m spacy download es_core_news_md

echo "🧠 Verificando base de datos..."
make status-db

echo "✅ Entorno listo. Puedes usar make test, make scrape, etc."