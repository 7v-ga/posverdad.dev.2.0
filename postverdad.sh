#!/bin/bash

# Script maestro del proyecto Postverdad
# Ejecuta scraping, verifica estado, genera resumen y notifica

set -e  # Detener en cualquier error

echo "🧼 Limpiando entorno anterior..."
make clean

echo "🧪 Verificando stack..."
make test

echo "🕸️ Ejecutando scraping..."
make scrape

echo "📈 Generando y notificando resumen..."
make notify-last

echo "✅ Pipeline completo ejecutado con éxito."
