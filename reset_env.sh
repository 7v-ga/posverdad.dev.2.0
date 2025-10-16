#!/bin/bash

echo "🧹 Eliminando entorno virtual..."
rm -rf venv

echo "🐍 Creando nuevo entorno virtual..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Actualizando pip y reinstalando dependencias..."
pip install --upgrade pip
pip install -r requirements-dev.txt -c constraints.txt

echo "📚 Descargando modelo spaCy..."
python -m spacy download es_core_news_md

echo "🧨 Reiniciando base de datos con make reset..."
make reset

echo "✅ Verificando con make test..."
make test

echo "🎉 Entorno limpio y listo para desarrollo."