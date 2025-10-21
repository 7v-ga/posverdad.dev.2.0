#!/usr/bin/env bash
set -euo pipefail

TSV="${1:-.github/labels.tsv}"

if ! command -v gh >/dev/null 2>&1; then
  echo "❌ Necesitas GitHub CLI (gh). Instala y autentica: gh auth login"
  exit 1
fi

if [ ! -f "$TSV" ]; then
  echo "❌ No encuentro $TSV"
  exit 1
fi

# Detecta owner/repo actuales
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
if [ -z "$REPO" ]; then
  echo "❌ No se pudo detectar el repo. Ejecuta dentro del repo o usa GH_REPO=owner/name"
  exit 1
fi
echo "📦 Repo: $REPO"

# Leer TSV (omite cabecera)
tail -n +2 "$TSV" | while IFS=$'\t' read -r NAME COLOR DESC; do
  [ -z "$NAME" ] && continue
  echo "➡️  $NAME (#$COLOR)"
  # Crea; si existe, edita (idempotente)
  if gh label create "$NAME" --color "$COLOR" --description "$DESC" --repo "$REPO" 2>/dev/null; then
    echo "   ✔️ creada"
  else
    gh label edit "$NAME" --color "$COLOR" --description "$DESC" --repo "$REPO" >/dev/null
    echo "   🔁 actualizada"
  fi
done

echo "✅ Etiquetas listas."
