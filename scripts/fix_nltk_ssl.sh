#!/bin/bash

# Uso: ./fix_nltk_ssl.sh path/a/python/bin/python

PYTHON_BIN="$1"

# Validación
if [ -z "$PYTHON_BIN" ]; then
  echo "❌ Debes pasar la ruta del ejecutable de Python. Ej: ./fix_nltk_ssl.sh venv/bin/python"
  exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
  echo "❌ El archivo '$PYTHON_BIN' no es ejecutable o no existe."
  exit 1
fi

echo "📍 Reinstalando certifi en entorno virtual..."
"$PYTHON_BIN" -m pip install --quiet --force-reinstall certifi

# Exportar ruta de certificados actual
export SSL_CERT_FILE=$("$PYTHON_BIN" -m certifi)
echo "🔐 Usando certificados desde: $SSL_CERT_FILE"

# Verificar si SSL está funcionando correctamente
"$PYTHON_BIN" -c "import ssl; import urllib.request; urllib.request.urlopen('https://www.google.com').read()" > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "⚠️ Error SSL detectado. Si persisten los errores, ejecuta manualmente el instalador oficial de certificados para macOS."
else
  echo "✅ Verificación SSL correcta. No se requiere instalación adicional."
fi

# Descargar corpora de NLTK sin warning
echo "📥 Descargando corpora de NLTK..."
"$PYTHON_BIN" -c "import nltk; [nltk.download(pkg) for pkg in ['punkt', 'brown', 'wordnet', 'averaged_perceptron_tagger', 'conll2000', 'movie_reviews']]"

echo "✅ Setup NLP completo."  
